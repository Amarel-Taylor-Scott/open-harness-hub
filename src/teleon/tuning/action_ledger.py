"""src.teleon.tuning.action_ledger — the append-only ACTION LEDGER for the self-tuning runtime layer.

Every runtime SELECTION is an ACTION: in some CONTEXT (the features the policy keys on) the runtime CHOSE
something (a model / route / component) and the run produced an OUTCOME (passed/failed, cost, latency, tokens).
This is the canonical, append-only, content-addressed record of every such action — the raw evidence the TUNER
(src.teleon.tuning.tuner) learns from CONTRASTIVELY (successful vs failed actions in similar contexts).

Design contract (matches the descent BRAIN and the egress ledger):
  * APPEND-ONLY = LOSSLESS — nothing is overwritten; FAILED actions are kept (a policy learner must learn from
    what did NOT work, not only the winners). Omitted/superseded != deleted.
  * CONTENT-ADDRESSED identity — ``action_id`` is a stable sha256 over the canonical bytes of the action, so a
    re-append of the same observation is an O(1) INDEXED idempotent no-op (never an O(n) rescan) and the stream
    scales past billions; a formatting change never forges a new identity, a content change always does.
  * BACKEND-SWAPPABLE — the durable store is the repo's ``record_store`` port (SQLite-WAL + JSONL mirror locally,
    Postgres/warehouse via config at scale). If that substrate is unavailable it degrades HONESTLY to a pure-Python
    append-only JSONL log with the same append/all/count contract — offline either way.
  * serves_truth=false — an action record is EVIDENCE, never a truth claim. Teleon-layer; never imports src.baltor.

Run:  PYTHONPATH=. python3 src/teleon/tuning/action_ledger.py --self-test
"""
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Run-as-script support: put the repo root on sys.path so ``import src.teleon.*`` resolves even when this
# file is executed directly (python3 src/teleon/tuning/action_ledger.py), not only as a package module.
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.experiments.ids import ID_HASH_SUFFIX_LEN, sha256_hex  # noqa: E402  single-source hash helpers

LEDGER_SCHEMA_VERSION = "TeleonActionLedger.v1"
ACTION_ID_PREFIX = "act"            #: human-readable prefix; the suffix is a content hash (never truncation-only)
SERVES_TRUTH = False                #: an action record is evidence, never a truth claim (CLAUDE.md governance)
_INDEX_DB_SUFFIX = ".idx.db"        #: co-located rebuildable SQLite index → writes never escape the ledger's dir


class ActionLedgerRejected(ValueError):
    """Raised when an append would violate the action-ledger contract (bad outcome, or a truth-bearing record)."""


@dataclass(frozen=True)
class ActionRecord:
    """One runtime ACTION: in ``context`` the runtime made ``choice`` and the run produced the outcome
    (``passed``/``cost``/``latency_ms``/``tokens``). ``context`` is the feature map the selection policy keys on;
    ``choice`` is what was selected — any of ``model`` / ``route`` / ``component`` (a subset is fine).

    ``occurred_at`` (a caller-supplied event time or monotone sequence) and ``run_id`` are part of the identity
    hash, so two genuinely-distinct events never collapse, while re-appending the SAME observation is idempotent.
    """

    task: str                                  # the capability/work the selection was for (e.g. "doc_extraction")
    context: dict[str, Any] = field(default_factory=dict)   # context features the policy keys on
    choice: dict[str, Any] = field(default_factory=dict)    # what was selected: model / route / component
    passed: bool = False                       # outcome: did the run satisfy its check?
    cost: float = 0.0                          # outcome: cost (USD) — lower is better
    latency_ms: float = 0.0                    # outcome: wall latency in ms — lower is better
    tokens: int = 0                            # outcome: tokens consumed — lower is better
    run_id: str = ""                           # lineage handle to the producing run
    occurred_at: str = ""                      # caller-supplied event time / monotone seq (part of identity)
    serves_truth: bool = SERVES_TRUTH

    def outcome(self) -> dict[str, Any]:
        """The outcome sub-record (passed/cost/latency/tokens) — the signal the tuner contrasts on."""
        return {"passed": bool(self.passed), "cost": float(self.cost),
                "latency_ms": float(self.latency_ms), "tokens": int(self.tokens)}

    def _identity(self) -> dict[str, Any]:
        return {"task": self.task, "context": self.context, "choice": self.choice,
                "outcome": self.outcome(), "run_id": self.run_id, "occurred_at": self.occurred_at}

    def action_id(self) -> str:
        """Stable content-addressed id ``act_<hash16>`` over the canonical bytes of the action (the idempotency key)."""
        return f"{ACTION_ID_PREFIX}_{sha256_hex(self._identity())[:ID_HASH_SUFFIX_LEN]}"

    def to_record(self) -> dict[str, Any]:
        """The full ledger record (self-describing): identity + schema version + serves_truth flag."""
        return {"schema_version": LEDGER_SCHEMA_VERSION, "action_id": self.action_id(),
                "task": self.task, "context": dict(self.context), "choice": dict(self.choice),
                "outcome": self.outcome(), "run_id": self.run_id, "occurred_at": self.occurred_at,
                "serves_truth": bool(self.serves_truth)}


class _JsonlFallbackStore:
    """Pure-Python append-only JSONL store honoring the record_store port (append/all/count), used ONLY when the
    SQLite-WAL substrate is unavailable. Idempotent by ``idem_key`` (an in-memory seen-set rebuilt from the file),
    append-only (a line is never rewritten), lossless, offline. Honest degradation — same on-disk contract."""

    backend = "jsonl_fallback"

    def __init__(self, jsonl_path: str | Path) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = set()
        if self.jsonl_path.exists():
            for line in self.jsonl_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    key = json.loads(line).get("_idem_key")
                    if key:
                        self._seen.add(key)

    def append(self, record: dict, *, idem_key: str | None = None) -> int:
        if idem_key is not None and idem_key in self._seen:
            return self.count()                       # O(1)-ish idempotent no-op (lossless: nothing overwritten)
        row = dict(record)
        if idem_key is not None:
            row["_idem_key"] = idem_key
            self._seen.add(idem_key)
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
        return self.count()

    def all(self, predicate=None) -> list[dict]:
        if not self.jsonl_path.exists():
            return []
        out = []
        for line in self.jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec.pop("_idem_key", None)                # the idem key is index metadata, not part of the record
            if predicate is None or predicate(rec):
                out.append(rec)
        return out

    def count(self) -> int:
        return len(self.all())

    def close(self) -> None:
        pass


def _open_store(jsonl_path: Path):
    """Open the append-only backing store. PRIMARY = the repo's backend-swappable ``LocalRecordStore`` (SQLite-WAL
    + durable JSONL mirror, O(1) content-addressed idempotency; the same record swaps to Postgres/warehouse by
    config). The rebuildable SQLite index is pinned NEXT TO the jsonl (``*.idx.db``) so a temp-path ledger never
    writes outside its own directory. If that substrate cannot be imported/opened, degrade HONESTLY to the
    pure-Python JSONL fallback with the identical append/all/count contract."""
    jsonl_path = Path(jsonl_path)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    db_path = jsonl_path.with_name(jsonl_path.name + _INDEX_DB_SUFFIX)
    try:
        from src.teleon.storage.record_store import LocalRecordStore
        return LocalRecordStore(jsonl_path, db_path=db_path)
    except Exception:
        return _JsonlFallbackStore(jsonl_path)


class ActionLedger:
    """Append-only, content-addressed ledger of runtime actions; idempotent by ``action_id``; lossless (keeps
    failures). Backed by the record_store port (honest JSONL fallback). serves_truth=false."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._store = None     # lazily opened so merely constructing the ledger creates no files

    def _open(self):
        if self._store is None:
            self._store = _open_store(self.path)
        return self._store

    @property
    def backend(self) -> str:
        """Which backend the store resolved to (``sqlite_wal`` or ``jsonl_fallback``) — honest about degradation."""
        return getattr(self._open(), "backend", "unknown")

    def append(self, action: ActionRecord) -> dict:
        """Append one action; IDEMPOTENT by content-hash ``action_id`` (re-appending the same observation is a no-op).
        Validates the outcome and refuses a truth-bearing record (an action is evidence, never truth)."""
        if not isinstance(action, ActionRecord):
            raise ActionLedgerRejected("append expects an ActionRecord")
        if action.serves_truth is not False:
            raise ActionLedgerRejected("action records must never serve truth (serves_truth must be False)")
        if not (isinstance(action.task, str) and action.task.strip()):
            raise ActionLedgerRejected("action.task must be a non-empty string")
        if not isinstance(action.context, dict) or not isinstance(action.choice, dict):
            raise ActionLedgerRejected("action.context and action.choice must be dicts")
        if not isinstance(action.passed, bool):
            raise ActionLedgerRejected("action.passed must be a bool (the run passed or failed)")
        for name, val in (("cost", action.cost), ("latency_ms", action.latency_ms), ("tokens", action.tokens)):
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0:
                raise ActionLedgerRejected(f"action.{name} must be a number >= 0")
        rec = action.to_record()
        self._open().append(rec, idem_key=rec["action_id"])     # O(1) idempotent content-addressed append
        return rec

    def extend(self, actions) -> int:
        """Append many actions; returns the number of DISTINCT records now in the ledger after the batch."""
        for a in actions:
            self.append(a)
        return self.count()

    def all(self) -> list[dict]:
        """Every action record, oldest-first. Empty (not an error) when nothing has been appended yet."""
        if self._store is None and not self.path.exists():
            return []
        return self._open().all()

    def count(self) -> int:
        """Live count of distinct action records."""
        if self._store is None and not self.path.exists():
            return 0
        return self._open().count()

    def stats(self) -> dict:
        """Aggregate readout (COMPUTED, never typed): per-(task, choice) n / pass-rate / mean cost — the raw shape
        the contrastive tuner ranks. Deterministic; offline."""
        by: dict[str, dict] = {}
        for r in self.all():
            choice_key = json.dumps(r.get("choice", {}), sort_keys=True, separators=(",", ":"))
            key = f"{r.get('task', '')}::{choice_key}"
            s = by.setdefault(key, {"task": r.get("task", ""), "choice": r.get("choice", {}),
                                    "n": 0, "passes": 0, "cost_sum": 0.0})
            out = r.get("outcome", {})
            s["n"] += 1
            s["passes"] += 1 if out.get("passed") else 0
            s["cost_sum"] += float(out.get("cost", 0.0))
        for s in by.values():
            s["pass_rate"] = round(s["passes"] / s["n"], 4) if s["n"] else 0.0
            s["mean_cost"] = round(s["cost_sum"] / s["n"], 6) if s["n"] else 0.0
            s.pop("cost_sum", None)
        return by

    def close(self) -> None:
        if self._store is not None:
            self._store.close()


def self_test() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="action_ledger_"))
    ledger = ActionLedger(tmp / "actions.jsonl")
    assert ledger.count() == 0 and ledger.all() == [], "a fresh ledger must be empty (not an error)"

    # A small deterministic action stream: in the SAME context, model A passes, model B fails.
    actions = [
        ActionRecord("doc_extraction", {"doc": "scanned_pdf", "lang": "en"}, {"model": "A", "route": "cheap"},
                     passed=True, cost=0.002, latency_ms=120.0, tokens=800, occurred_at="t0"),
        ActionRecord("doc_extraction", {"doc": "scanned_pdf", "lang": "en"}, {"model": "B", "route": "cheap"},
                     passed=False, cost=0.001, latency_ms=90.0, tokens=600, occurred_at="t1"),
        ActionRecord("doc_extraction", {"doc": "scanned_pdf", "lang": "en"}, {"model": "A", "route": "cheap"},
                     passed=True, cost=0.002, latency_ms=130.0, tokens=820, occurred_at="t2"),
    ]
    n = ledger.extend(actions)
    assert n == 3, f"three distinct actions expected, got {n}"

    # Content-addressed identity is stable + deterministic.
    aid = actions[0].action_id()
    assert aid.startswith(ACTION_ID_PREFIX + "_") and actions[0].action_id() == aid, "action_id must be stable"

    # Idempotent: re-appending the SAME observation is a no-op (append-only = lossless, nothing duplicated).
    ledger.append(actions[0])
    assert ledger.count() == 3, "re-appending an identical action must NOT create a new row (content-hash idem)"

    # A distinct event (different occurred_at) is a NEW record — distinct events never collapse.
    ledger.append(ActionRecord("doc_extraction", {"doc": "scanned_pdf", "lang": "en"}, {"model": "A", "route": "cheap"},
                               passed=True, cost=0.002, latency_ms=125.0, tokens=810, occurred_at="t3"))
    assert ledger.count() == 4, "a genuinely distinct action (new occurred_at) must be its own record"

    # Records are self-describing + clean (no index metadata leaks into the record body).
    recs = ledger.all()
    assert all(set(r) >= {"action_id", "task", "context", "choice", "outcome", "serves_truth"} for r in recs)
    assert all(r["serves_truth"] is False for r in recs), "every action record serves_truth=False"
    assert all("_idem_key" not in r for r in recs), "the idempotency key is index metadata, never the record body"

    # Stats are COMPUTED: model A passed twice (pass_rate 1.0), model B failed once (0.0).
    stats = ledger.stats()
    a_key = next(k for k, v in stats.items() if v["choice"].get("model") == "A")
    b_key = next(k for k, v in stats.items() if v["choice"].get("model") == "B")
    assert stats[a_key]["pass_rate"] == 1.0 and stats[b_key]["pass_rate"] == 0.0, "pass-rates must be computed"

    # Lossless / durable: a fresh ledger over the same path reads the same records back (append-only persisted).
    reopened = ActionLedger(tmp / "actions.jsonl")
    assert reopened.count() == 4, "the append-only ledger must persist across reopen (lossless)"

    # Governance: truth-bearing records and malformed outcomes are REFUSED, honestly.
    refused = 0
    for bad in (
        ActionRecord("t", {}, {}, passed=True, serves_truth=True),       # truth-bearing → rejected
        ActionRecord("", {}, {}, passed=True),                            # empty task → rejected
        ActionRecord("t", {}, {}, passed=True, cost=-1.0),                # negative cost → rejected
    ):
        try:
            ledger.append(bad)
        except ActionLedgerRejected:
            refused += 1
    assert refused == 3, f"the ledger must refuse all 3 contract violations, refused {refused}"

    # Honest degradation: the pure-Python fallback honors the same append/all/count + idempotency contract.
    fb = _JsonlFallbackStore(tmp / "fallback.jsonl")
    fb.append({"action_id": "x", "v": 1}, idem_key="x")
    fb.append({"action_id": "x", "v": 1}, idem_key="x")     # idempotent
    assert fb.count() == 1 and fb.backend == "jsonl_fallback", "fallback must be idempotent + honestly named"

    print(f"action_ledger self-test: OK (backend={ledger.backend} · {ledger.count()} actions · "
          f"content-hash idempotent · append-only/lossless · {refused} contract violations refused)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: action_ledger --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
