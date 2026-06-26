"""src.teleon.storage.sync_engine — a MULTI-LOCATION SYNC engine with leaf-shard scaling.

Many of the same records live in more than one LOCATION at once — the git tree that authors them, the
operational db that serves them, the object store that mirrors them for cold reads. Keeping those copies
in agreement is a content-addressed, CDC-driven, idempotent motion — not a destructive copy:

  * CONTENT-HASH change detection — every record carries a stable ``content_hash`` (sha256 over canonical
    JSON of its body). A location's copy "changed" iff its hash moved; an unchanged copy is an O(1) no-op,
    never a re-scan. This is the same idempotency key the append-only ``record_store`` uses at every tier.
  * CDC propagation, IDEMPOTENT — each distinct ``(op, record_id, content_hash)`` state-transition is ONE
    append-only CDC event (content-addressed event_id → re-capture dedupes). Re-running ``sync()`` after
    convergence captures zero new events and applies zero writes; the locations stay in lock-step.
  * LEAF-SHARDING — records are placed by a HASH PREFIX of their id (``shard_of``). A K-hex-char prefix is
    a leaf shard; widening the prefix multiplies the keyspace ×16 per char (8 hex chars ≈ 4.3e9 leaves),
    so the same code scales from thousands toward billions of records without a re-key.
  * GOVERNED conflict handling — divergence is detected against the last-converged BASELINE (common
    ancestor). One side advanced + the rest stale → a clean fast-forward. Two sides advanced divergently
    (same id, divergent hashes) → a CONFLICT: it is FLAGGED for review, never silently clobbered, and the
    CDC log keeps BOTH states (lossless). serves_truth=false on everything — a synced copy is evidence of
    a state, never a truth claim.

The cloud swap mirrors ``record_store``: here the locations are in-memory stores (offline + deterministic
test doubles); in production each ``Location`` is a backend behind the same port (git / Postgres / object
store) and the CDC log lands on the append-only history tier. The record schema + idempotency key are
backend-independent, so the swap is a loader/config change, never a caller change.

Teleon-layer — never imports src.baltor.

  PYTHONPATH=. python3 src/teleon/storage/sync_engine.py --self-test
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Insert repo root on sys.path so the module runs as a plain script (PYTHONPATH=. python3 …/sync_engine.py).
REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: content-hash algorithm — the single idempotency key shared with record_store / the CDC tier.
CONTENT_HASH_ALGO = "sha256"
#: hex chars of the record-id hash that name a leaf shard. 4 → 16**4 = 65,536 leaves; widen to scale
#: (each added hex char ×16 the keyspace; 8 → 16**8 ≈ 4.29e9 leaves — billions — same code path).
DEFAULT_SHARD_PREFIX_LEN = 4


# -- content addressing + sharding (pure, deterministic) ------------------------------------------
def _canonical_json(value: object) -> str:
    """Canonical JSON so formatting can never forge a false hash (sorted keys, tight separators, ascii)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def content_hash(body: object) -> str:
    """Stable ``sha256:<hex>`` over a record's canonical body — the content-addressed identity + idem key."""
    return CONTENT_HASH_ALGO + ":" + hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def shard_of(record_id: str, *, prefix_len: int = DEFAULT_SHARD_PREFIX_LEN) -> str:
    """The LEAF shard a record lands in: a fixed-width hex PREFIX of sha256(record_id). Deterministic and
    uniform; widening ``prefix_len`` grows the leaf keyspace ×16 per char (the billion-row scale path)."""
    if prefix_len < 1:
        raise ValueError(f"prefix_len must be >= 1, got {prefix_len}")
    digest = hashlib.sha256(record_id.encode("utf-8")).hexdigest()
    return "leaf-" + digest[:prefix_len]


def shard_keyspace(prefix_len: int = DEFAULT_SHARD_PREFIX_LEN) -> int:
    """Number of leaf shards a given prefix width addresses (16**prefix_len)."""
    return 16 ** prefix_len


def _event_id(op: str, record_id: str, ch: str) -> str:
    """Content-addressed CDC event id — identical state-transitions collapse to one event (idempotency)."""
    return "cdc:" + hashlib.sha256(f"{op}|{record_id}|{ch}".encode("utf-8")).hexdigest()[:24]


def _conflict_id(record_id: str, hashes) -> str:
    """Content-addressed review-ticket id — re-flagging the SAME divergence does not duplicate the ticket."""
    key = record_id + "|" + "|".join(sorted(hashes))
    return "review:conflict:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


# -- records, locations, the CDC log --------------------------------------------------------------
@dataclass
class Record:
    """One record's CURRENT materialized state in a location. ``content_hash`` is derived from ``body``."""
    record_id: str
    body: dict
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.content_hash = content_hash(self.body)


class Location:
    """An in-memory store standing in for a sync location (git / db / object_store / …). In production this
    is a backend behind the record_store port; the sync motion is identical. serves_truth=false."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.records: dict[str, Record] = {}

    def put(self, record_id: str, body: dict) -> Record:
        rec = Record(record_id, dict(body))
        self.records[record_id] = rec
        return rec

    def get(self, record_id: str) -> Record | None:
        return self.records.get(record_id)

    def hash_of(self, record_id: str) -> str | None:
        rec = self.records.get(record_id)
        return rec.content_hash if rec else None

    def snapshot(self) -> dict[str, str]:
        """id → content_hash for the whole location (the comparable state)."""
        return {rid: rec.content_hash for rid, rec in sorted(self.records.items())}


@dataclass(frozen=True)
class CDCEvent:
    """An append-only change-data-capture event: a state-transition, content-addressed for idempotency."""
    seq: int
    event_id: str
    op: str            # "upsert" (the only mutation here; the op field leaves room for tombstones)
    record_id: str
    content_hash: str
    source_location: str
    shard: str
    serves_truth: bool = False

    def as_dict(self) -> dict:
        return {"seq": self.seq, "event_id": self.event_id, "op": self.op, "record_id": self.record_id,
                "content_hash": self.content_hash, "source_location": self.source_location,
                "shard": self.shard, "serves_truth": False}


class CDCLog:
    """Append-only, LOSSLESS change log. ``append`` is idempotent on the content-addressed event_id — the
    SAME state-transition (re-seen on any location, on any re-sync) is a no-op, so deltas never duplicate."""

    def __init__(self) -> None:
        self._events: list[CDCEvent] = []
        self._seen: set[str] = set()

    def append(self, *, op: str, record_id: str, content_hash: str, source_location: str, shard: str) -> CDCEvent | None:
        ev_id = _event_id(op, record_id, content_hash)
        if ev_id in self._seen:
            return None  # idempotent: this exact transition is already on the log
        ev = CDCEvent(seq=len(self._events), event_id=ev_id, op=op, record_id=record_id,
                      content_hash=content_hash, source_location=source_location, shard=shard)
        self._events.append(ev)
        self._seen.add(ev_id)
        return ev

    def events(self, predicate=None) -> list[CDCEvent]:
        return [e for e in self._events if predicate is None or predicate(e)]

    def hashes_for(self, record_id: str) -> set[str]:
        """Every content_hash the log has ever captured for a record (the lossless state history)."""
        return {e.content_hash for e in self._events if e.record_id == record_id}

    def count(self) -> int:
        return len(self._events)


# -- the sync engine ------------------------------------------------------------------------------
class SyncEngine:
    """Keep >=2 LOCATIONS in agreement via content-hash change detection + an idempotent CDC log, leaf-
    sharded for scale, with GOVERNED (flag-don't-clobber) conflict handling. serves_truth=false."""

    def __init__(self, location_names) -> None:
        names = list(location_names)
        if len(names) < 2:
            raise ValueError(f"sync needs >= 2 locations, got {names}")
        self.locations: dict[str, Location] = {n: Location(n) for n in names}
        self.cdc = CDCLog()
        self.blobs: dict[str, dict] = {}                 # content_hash -> body (content-addressed, dedup)
        self.conflicts: dict[str, dict] = {}             # conflict_id -> open review ticket
        self.baseline: dict[str, str] = {}               # record_id -> last-converged hash (common ancestor)

    def location(self, name: str) -> Location:
        return self.locations[name]

    # -- phase 1: capture content-hash changes onto the CDC log (idempotent) -----------------------
    def _capture(self) -> list[CDCEvent]:
        captured: list[CDCEvent] = []
        for loc in self.locations.values():
            for rec in loc.records.values():
                self.blobs.setdefault(rec.content_hash, dict(rec.body))   # content-addressed body store
                ev = self.cdc.append(op="upsert", record_id=rec.record_id, content_hash=rec.content_hash,
                                     source_location=loc.name, shard=shard_of(rec.record_id))
                if ev is not None:                       # None == already-seen transition (idempotent)
                    captured.append(ev)
        return captured

    # -- phase 2: resolve desired state per record + apply (fast-forward) or flag (conflict) -------
    def _resolve_and_apply(self) -> tuple[int, int, list[dict]]:
        applied = fast_forwards = 0
        open_conflicts: list[dict] = []
        all_ids = sorted({rid for loc in self.locations.values() for rid in loc.records})
        for rid in all_ids:
            present = {name: loc.records[rid].content_hash
                       for name, loc in self.locations.items() if rid in loc.records}
            distinct = set(present.values())
            if len(distinct) == 1:
                winner = next(iter(distinct))            # all present copies agree (incl. the new-record case)
            else:
                baseline = self.baseline.get(rid)
                advanced = {h for h in distinct if h != baseline}
                if len(advanced) != 1:
                    # >=2 sides moved off the common ancestor divergently (or no ancestor + >=2 creates):
                    # a genuine CONFLICT — flag for review, clobber NOTHING, keep both states on the log.
                    open_conflicts.append(self._flag_conflict(rid, present))
                    continue
                winner = next(iter(advanced))            # exactly one side advanced; rest are stale → fast-forward
                fast_forwards += 1
            winner_body = self.blobs[winner]
            for loc in self.locations.values():          # propagate the winner everywhere (idempotent at winner)
                if loc.hash_of(rid) != winner:
                    loc.put(rid, winner_body)
                    applied += 1
            self.baseline[rid] = winner                  # record the new common ancestor
        return applied, fast_forwards, open_conflicts

    def _flag_conflict(self, record_id: str, present: dict[str, str]) -> dict:
        cid = _conflict_id(record_id, present.values())
        existing = self.conflicts.get(cid)
        if existing is not None:
            return existing                              # idempotent: same divergence is not re-ticketed
        ticket = {
            "review_ticket_id": cid,
            "kind": "sync_conflict",
            "record_id": record_id,
            "shard": shard_of(record_id),
            "divergent": dict(sorted(present.items())),  # location -> its (divergent) content_hash
            "baseline": self.baseline.get(record_id),    # the common ancestor, if any
            "status": "open",
            "resolution": "manual_review",               # GOVERNED: never auto-clobbered
            "serves_truth": False,
        }
        self.conflicts[cid] = ticket
        return ticket

    def sync(self) -> dict:
        """One sync pass: capture content-hash deltas → CDC log, then converge every location (fast-forward)
        or flag divergence for review. Idempotent: re-running after convergence is an all-no-op pass."""
        captured = self._capture()
        applied, fast_forwards, open_conflicts = self._resolve_and_apply()
        return {
            "ok": True,
            "locations": sorted(self.locations),
            "captured_events": len(captured),
            "applied_writes": applied,
            "fast_forwards": fast_forwards,
            "conflicts_flagged": len(open_conflicts),
            "open_conflicts": sum(1 for t in self.conflicts.values() if t["status"] == "open"),
            "cdc_event_count": self.cdc.count(),
            "converged": applied == 0 and not open_conflicts,
            "serves_truth": False,
        }

    # -- sharding helper ---------------------------------------------------------------------------
    def shard_assignment(self, record_ids, *, prefix_len: int = DEFAULT_SHARD_PREFIX_LEN) -> dict[str, list[str]]:
        """Group record ids by their leaf shard (deterministic). Shows records land in stable shards."""
        out: dict[str, list[str]] = {}
        for rid in record_ids:
            out.setdefault(shard_of(rid, prefix_len=prefix_len), []).append(rid)
        return {k: sorted(v) for k, v in sorted(out.items())}


# -- self-test ------------------------------------------------------------------------------------
def self_test() -> int:
    # ---- A) idempotent convergence across locations -------------------------------------------------
    eng = SyncEngine(["git", "db", "object_store"])
    seed = {f"component/rec-{i}": {"name": f"rec-{i}", "score": i} for i in range(4)}
    for rid, body in seed.items():
        eng.location("git").put(rid, body)               # authored in git only

    s1 = eng.sync()
    assert s1["captured_events"] == 4, f"first sync should capture 4 deltas, got {s1}"
    assert s1["cdc_event_count"] == 4, s1
    snaps = [eng.location(n).snapshot() for n in ("git", "db", "object_store")]
    assert snaps[0] == snaps[1] == snaps[2], f"all locations must converge, got {snaps}"
    assert len(snaps[0]) == 4, snaps[0]

    s2 = eng.sync()                                       # re-run: must be a total no-op (idempotent)
    assert s2["captured_events"] == 0 and s2["applied_writes"] == 0, f"re-sync must be a no-op, got {s2}"
    assert s2["cdc_event_count"] == 4, f"CDC log must not duplicate, got {s2}"
    assert s2["converged"] is True, s2

    # ---- B) content-hash change detection (one record moves on one location) ------------------------
    rid = "component/rec-2"
    old_hash = eng.location("db").hash_of(rid)
    eng.location("db").put(rid, {"name": "rec-2", "score": 999})   # change body → hash moves
    new_hash = eng.location("db").hash_of(rid)
    assert new_hash != old_hash, "changed body must yield a new content_hash"

    s3 = eng.sync()
    assert s3["captured_events"] == 1, f"only the one changed record is a delta, got {s3}"
    assert s3["fast_forwards"] == 1 and s3["conflicts_flagged"] == 0, s3
    for n in ("git", "db", "object_store"):
        assert eng.location(n).hash_of(rid) == new_hash, f"{n} must fast-forward to the new hash"
    assert eng.location("git").hash_of("component/rec-0") == snaps[0]["component/rec-0"], "untouched record unchanged"
    assert eng.cdc.count() == 5, f"exactly one new CDC event appended, got {eng.cdc.count()}"

    # ---- C) deterministic leaf-sharding -------------------------------------------------------------
    assert shard_of("component/rec-2") == shard_of("component/rec-2"), "shard_of must be deterministic"
    ids = [f"component/rec-{i}" for i in range(200)]
    a1 = eng.shard_assignment(ids)
    a2 = eng.shard_assignment(ids)
    assert a1 == a2, "shard assignment must be stable across calls"
    assert len(a1) > 1, "200 ids must distribute across multiple leaf shards"
    assert all(rid in a1[shard_of(rid)] for rid in ids), "every id must land in its own deterministic shard"
    assert shard_keyspace(4) == 65536 and shard_keyspace(8) == 4294967296, "leaf keyspace scales toward billions"
    assert len(shard_of("x", prefix_len=8)) == len("leaf-") + 8, "widening the prefix widens the leaf id"

    # ---- D) governed conflict flagging (same id, divergent hashes → flag, never clobber) ------------
    c = SyncEngine(["git", "db"])
    c.location("git").put("component/dup", {"name": "dup", "owner": "alice"})   # divergent creates,
    c.location("db").put("component/dup", {"name": "dup", "owner": "bob"})      # no common ancestor
    git_h = c.location("git").hash_of("component/dup")
    db_h = c.location("db").hash_of("component/dup")
    assert git_h != db_h

    cs1 = c.sync()
    assert cs1["conflicts_flagged"] == 1 and cs1["open_conflicts"] == 1, f"divergence must be flagged, got {cs1}"
    assert c.location("git").hash_of("component/dup") == git_h, "git side must NOT be clobbered"
    assert c.location("db").hash_of("component/dup") == db_h, "db side must NOT be clobbered"
    ticket = next(iter(c.conflicts.values()))
    assert ticket["status"] == "open" and ticket["serves_truth"] is False and ticket["resolution"] == "manual_review", ticket
    assert set(ticket["divergent"].values()) == {git_h, db_h}, ticket
    assert c.cdc.hashes_for("component/dup") == {git_h, db_h}, "CDC log must keep BOTH states (lossless)"

    cs2 = c.sync()                                        # re-sync: same conflict, NOT re-ticketed
    assert cs2["open_conflicts"] == 1 and len(c.conflicts) == 1, f"conflict must not duplicate, got {cs2}"
    assert cs2["captured_events"] == 0, "no new CDC events on a re-sync of a known conflict"

    print("sync_engine self-test: OK (idempotent convergence · content-hash deltas · deterministic "
          "leaf-shards · governed conflict flagging · lossless CDC; serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: sync_engine --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
