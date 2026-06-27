"""src.teleon.compiler.registry — the durable, append-only REGISTRY of compiled runtime units.

THE GAP THIS CLOSES (docs/strategy/teleon-self-improving-runtime-vision.md §Stage 5/6 GAP (d);
docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md step 4): the compiler turns a PROMOTED
capability into a ``CompiledRuntimeUnit`` (``compile.py``) and ``emit.py`` renders it to fly/k8s/local — but
**nothing persisted which capability-version is compiled to which runtime**. There was no per-CAPABILITY analog
of the per-SERVICE ``architecture/deploy_topology.json``: no way to ask "what is the latest compiled unit for
capability X", to roll back to its predecessor, or to drive auto-deploy-on-promotion. This module IS that
registry — the "registry of promoted runtimes" Stage 6 promised.

WHAT IT IS — an append-only EVENT LOG of two record kinds, folded into current state on read:
  * a ``register`` event carries the full compiled unit + registry metadata (it becomes the ACTIVE unit for its
    capability and DEMOTES the prior active one — that prior unit becomes the new unit's ``rollback_target``);
  * a ``demote`` event marks a unit no longer active WITHOUT deleting it (lossless: superseded units stay in the
    log, queryable via ``history`` — demote-not-delete).
The current registry state (which unit is active per capability, the full history, the rollback target) is a
deterministic fold over the log — exactly the latest-line-wins idiom the runtime's ``runs.jsonl`` already uses.

DURABILITY — backed by the repo's append-log engine (``scripts._jsonl_store.AppendLog``): a SQLite-WAL primary
(crash-safe, one ACID txn per append) behind an append-only ``*.jsonl`` MIRROR that is the contracted on-disk
record. On a cold start the engine REBUILDS its index from the JSONL, so on a host whose only durable volume is
the state dir (a Fly Machine volume), the JSONL on the volume is the source of truth and the registry rehydrates
to EQUAL state for free. The JSONL lives under ``dist/local-services-state/teleon-compiler/`` — the same
``dist/local-services-state/<service>`` mount pattern every Teleon local service uses (the registry record is the
deploy_topology analog, so it lives next to the runtime state it describes).

ROLLBACK IS REAL — the ``rollback_target`` field the compiler carries was, until now, *carried but never
consumable*: nothing held the predecessor to roll back TO. The registry makes it real: ``register`` stamps the
prior active unit's ``unit_id`` into the new unit's ``rollback_target`` (overriding any caller value — the
registry is the authority on what the real predecessor is), and ``rollback_target`` / ``rollback_to`` return /
activate that exact prior unit. A capability with no predecessor honestly reports no rollback target.

LAWS:
  * LOSSLESS (docs/codex/lossless-distillation.md): superseded units are DEMOTED, never deleted — full history is
    preserved + queryable, and the rollback target is always a real preserved unit, never a reconstruction.
  * DETERMINISTIC: the registry reads no clock and no random. ``registered_at`` is the unit's own
    ``provenance.compiled_at`` (caller-supplied); ordering is by ``(capability_version, compiled_at, unit_id)`` —
    a total order with deterministic tie-breaks, so a rebuild from the same log is byte-identical.
  * IDEMPOTENT: ``register`` is keyed by ``unit_id`` (which is itself a pure hash of the compile inputs);
    re-registering the same unit is a no-op that returns the existing record — a daily recompile of unchanged
    inputs does not grow the active set or fork the rollback chain.
  * HONEST: the registry stores deployable PLANS (``is_truth:false`` units). It is NOT the source of truth about
    a capability's gate status — the FleetLedger / capability gate remain that. ``rebuild`` / ``rollback_target``
    fail with a clear error on a tampered or structurally-broken log rather than silently returning a wrong unit.

ARCHITECTURAL LAW — Teleon-layer code: imports only stdlib + ``src.teleon`` siblings + ``scripts`` tooling
(``scripts._jsonl_store`` — an offline durability engine, NOT a brand layer; ``src/teleon`` already depends on
``scripts.*`` in ``compiler/live_capability.py`` and ``experiments/*``). It never imports ``src.baltor`` /
``src.openhubforai`` (the portfolio dependency law; proven by ``--self-test`` and
``scripts/check_portfolio_dependency_law.py``).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

# scripts._jsonl_store is the repo's append-log durability engine (SQLite-WAL primary + append-only JSONL mirror,
# rebuild-on-cold-start from the JSONL). It is TOOLING, not a brand layer — importing it from src.teleon does not
# cross the portfolio dependency law (same as compiler/live_capability.py importing scripts.teleon_local_runtime).
from scripts._jsonl_store import AppendLog

_REPO = Path(__file__).resolve().parents[3]

# ── single-source constants (no-magic-values) ────────────────────────────────────────────────────────────────
#: the registry's own schema/format version — surfaced in every record so a later format change is attributable.
REGISTRY_RECORD_VERSION = "CompiledUnitRegistryRecord"
#: the two record kinds in the append-only log. A `register` adds/activates a unit (demoting the prior active
#: one); a `demote` marks a unit inactive WITHOUT deleting it (lossless supersession). ONE definition each.
KIND_REGISTER = "register"
KIND_DEMOTE = "demote"
RECORD_KINDS = (KIND_REGISTER, KIND_DEMOTE)

#: the durable JSONL lives under the SAME dist/local-services-state/<service> mount every Teleon local service
#: uses (scripts/teleon_local_runtime.py STATE_DIR = dist/local-services-state/teleon-runtime). The registry is
#: the per-capability deploy_topology analog, so it sits beside the runtime state it describes. ONE definition;
#: the doc + the Fly volume mount note point here. (On Fly this dir is the machine's mounted volume; the SQLite
#: index AppendLog keeps under .agent/ is rebuilt from this JSONL on cold start — the JSONL is the truth.)
DEFAULT_STATE_DIR = _REPO / "dist" / "local-services-state" / "teleon-compiler"
DEFAULT_LOG_NAME = "compiled-units.jsonl"

#: the unit fields the registry treats as the lineage/ordering key (all read off the compiled unit — never
#: re-typed here). capability_version + compiled_at + unit_id give a TOTAL deterministic order with stable
#: tie-breaks (so two units compiled at the same stamped instant still order deterministically by unit_id).
_UNIT_ID = "unit_id"
_CAP_ID = "capability_id"
_CAP_VERSION = "capability_version"
_ROLLBACK_TARGET = "rollback_target"
_COMPILED_AT = ("provenance", "compiled_at")  # nested path into the unit


class RegistryError(Exception):
    """Base for registry refusals — a clear, actionable reason, never a silently-wrong answer."""


class RegistryIntegrityError(RegistryError):
    """The append-only log is structurally broken / tampered (a record missing its kind, a register event with no
    unit, a unit missing its id, a demote naming a unit that was never registered). The registry refuses to fold
    a corrupt log into state rather than return a wrong/partial unit (HONEST: fail loudly, don't guess)."""


def _get_path(unit: dict, path: tuple[str, ...]) -> Any:
    cur: Any = unit
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _compiled_at(unit: dict) -> str:
    """The unit's caller-supplied compile timestamp (provenance.compiled_at). '' when absent — a deterministic
    sort still works (empty sorts first); the registry never invents a clock value."""
    val = _get_path(unit, _COMPILED_AT)
    return "" if val is None else str(val)


def _order_key(unit: dict) -> tuple[Any, str, str]:
    """Deterministic TOTAL order for a capability's units: by capability_version, then the stamped compiled_at,
    then unit_id (a stable tie-break). version is normalized to (is_present, value) so a missing/None version
    sorts before any real one without raising on a None-vs-int comparison."""
    ver = unit.get(_CAP_VERSION)
    ver_key: tuple[int, float] = (0, 0.0) if ver is None else (1, float(ver))
    return (ver_key, _compiled_at(unit), str(unit.get(_UNIT_ID, "")))


class CompiledUnitRegistry:
    """An append-only registry of compiled runtime units — the per-capability deploy_topology analog.

    The on-disk record is an append-only JSONL (durable, the Fly-volume source of truth) of ``register`` /
    ``demote`` events; current state (active unit per capability, full history, rollback target) is a
    deterministic fold over the log, recomputed on construction (rebuild-on-start) and kept in sync as events are
    appended. Backed by ``scripts._jsonl_store.AppendLog`` (SQLite-WAL primary + JSONL mirror) so a crash mid-append
    cannot corrupt it and a restart rehydrates to EQUAL state.
    """

    def __init__(self, log_path: Path | str | None = None, *, db_path: Path | None = None) -> None:
        self.log_path = Path(log_path) if log_path is not None else (DEFAULT_STATE_DIR / DEFAULT_LOG_NAME)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # AppendLog rebuilds its SQLite index from this JSONL on a cold start, so the JSONL is the durable truth.
        self._log = AppendLog(self.log_path, db_path=db_path)
        # in-memory projection, recomputed from the full log (rebuild-on-start); kept in sync on each append.
        self._records: list[dict] = []
        self.rebuild()

    # ── projection / rebuild (deterministic fold over the append-only log) ────────────────────────────────────
    def rebuild(self) -> None:
        """(Re)compute the in-memory projection from the FULL append-only log. Called on construction
        (rehydration) and after each append. Validates every record's structure — a corrupt/tampered log raises
        ``RegistryIntegrityError`` rather than yielding a wrong fold (HONEST). Pure: same log → same projection."""
        records = list(self._log.iter())
        self._validate_log(records)
        self._records = records

    @staticmethod
    def _validate_log(records: list[dict]) -> None:
        """Structural integrity check over the whole log (HONEST: refuse a broken log, don't guess).
        Every record has a known ``kind``; a ``register`` carries a unit with a ``unit_id`` + ``capability_id``;
        a ``demote`` names a ``unit_id`` that some earlier ``register`` introduced (you cannot demote a unit that
        was never registered — that is a tampered/torn log)."""
        registered_ids: set[str] = set()
        for i, rec in enumerate(records):
            kind = rec.get("kind")
            if kind not in RECORD_KINDS:
                raise RegistryIntegrityError(
                    f"registry log record #{i} has kind {kind!r}, not one of {RECORD_KINDS} — the log is corrupt")
            if kind == KIND_REGISTER:
                unit = rec.get("unit")
                if not isinstance(unit, dict) or not unit.get(_UNIT_ID):
                    raise RegistryIntegrityError(
                        f"registry log record #{i} is a {KIND_REGISTER!r} with no unit/unit_id — the log is corrupt")
                if not unit.get(_CAP_ID):
                    raise RegistryIntegrityError(
                        f"registry log record #{i} unit {unit.get(_UNIT_ID)!r} has no capability_id — corrupt log")
                registered_ids.add(str(unit[_UNIT_ID]))
            else:  # KIND_DEMOTE
                uid = rec.get("unit_id")
                if not uid:
                    raise RegistryIntegrityError(
                        f"registry log record #{i} is a {KIND_DEMOTE!r} with no unit_id — the log is corrupt")
                if str(uid) not in registered_ids:
                    raise RegistryIntegrityError(
                        f"registry log record #{i} demotes unit {uid!r} that was never registered — the log is "
                        "tampered/torn (a demote must follow the register it supersedes)")

    def _unit_records(self) -> list[dict]:
        """The ``register`` records, in log (append) order — the source for the per-unit projection. The LAST
        register for a given unit_id wins (idempotent re-register replays the same content; a deliberate
        re-register of a re-compiled unit with the same id is the same unit)."""
        by_id: dict[str, dict] = {}
        for rec in self._records:
            if rec.get("kind") == KIND_REGISTER:
                by_id[str(rec["unit"][_UNIT_ID])] = rec
        return list(by_id.values())

    def _active_ids(self) -> set[str]:
        """The set of unit_ids currently ACTIVE = registered AND not subsequently demoted. Folded in log order so
        a later ``register`` of a unit (idempotent) re-activates it and a later ``demote`` deactivates it."""
        active: set[str] = set()
        for rec in self._records:
            kind = rec.get("kind")
            if kind == KIND_REGISTER:
                active.add(str(rec["unit"][_UNIT_ID]))
            elif kind == KIND_DEMOTE:
                active.discard(str(rec["unit_id"]))
        return active

    # ── write path ────────────────────────────────────────────────────────────────────────────────────────────
    def register(self, unit: dict, *, make_active: bool = True) -> dict:
        """Register a compiled unit. IDEMPOTENT by ``unit_id`` (a pure hash of the compile inputs): re-registering
        the same unit is a no-op that returns the EXISTING record (a daily recompile of unchanged inputs does not
        grow the active set or fork the rollback chain).

        On a NEW unit with ``make_active`` (the default): the prior ACTIVE unit for the same capability is
        DEMOTED (lossless — it stays in the log, queryable) and its ``unit_id`` is stamped into THIS unit's
        ``rollback_target`` (the registry is the authority on the real predecessor — it overrides any caller
        value). That makes rollback real: ``rollback_target(capability_id)`` returns that exact prior unit.

        Returns the stored registry RECORD (``{kind, record_version, unit, active, registered_at, rollback_target,
        supersedes}``). Deterministic: ``registered_at`` is the unit's own ``provenance.compiled_at`` — the
        registry reads no clock.
        """
        if not isinstance(unit, dict):
            raise RegistryError("register expects a compiled unit dict")
        unit_id = unit.get(_UNIT_ID)
        capability_id = unit.get(_CAP_ID)
        if not unit_id:
            raise RegistryError("compiled unit has no unit_id — cannot register (compile it first)")
        if not capability_id:
            raise RegistryError(f"compiled unit {unit_id!r} has no capability_id — cannot register")

        existing = self.get(str(unit_id))
        if existing is not None:
            return existing  # IDEMPOTENT: same unit_id → the existing record, unchanged (no duplicate append)

        # the predecessor to roll back TO = the current ACTIVE unit for this capability (None for the first one).
        predecessor = self.latest_active_for(str(capability_id)) if make_active else None
        predecessor_id = str(predecessor[_UNIT_ID]) if predecessor is not None else ""

        # the registry OWNS rollback_target: stamp the real predecessor (deep-copy the unit so we never mutate the
        # caller's object, and so the stored record is self-contained + lossless).
        stored_unit = json.loads(json.dumps(unit))
        stored_unit[_ROLLBACK_TARGET] = predecessor_id

        record = {
            "kind": KIND_REGISTER,
            "record_version": REGISTRY_RECORD_VERSION,
            "unit": stored_unit,
            "active": bool(make_active),
            # deterministic: the unit's caller-supplied compile timestamp, never a wall clock read here.
            "registered_at": _compiled_at(stored_unit),
            "rollback_target": predecessor_id,
            "supersedes": predecessor_id,  # explicit lineage to the unit this one supersedes ('' if first)
        }

        # demote the predecessor FIRST (lossless: a demote event, not a deletion), then register the new unit, so
        # at no fold point are two units for the same capability simultaneously active.
        if make_active and predecessor is not None:
            self._append({"kind": KIND_DEMOTE, "record_version": REGISTRY_RECORD_VERSION,
                          "unit_id": predecessor_id, "demoted_by": str(unit_id),
                          "reason": "superseded by a newer compiled unit for the same capability",
                          "demoted_at": record["registered_at"]})
        self._append(record)
        return self.get(str(unit_id)) or record

    def supersede(self, unit_id: str, *, demoted_by: str = "", reason: str = "manual supersede") -> dict:
        """Demote a unit by id WITHOUT deleting it (lossless supersession). The unit stays in ``history``; it is
        simply no longer ``active``. Idempotent: demoting an already-inactive unit is a no-op. Raises if the unit
        was never registered (you cannot demote what does not exist — HONEST)."""
        uid = str(unit_id)
        if self.get(uid) is None:
            raise RegistryError(f"cannot supersede unit {uid!r} — it was never registered")
        if uid not in self._active_ids():
            return self.get(uid)  # already inactive — idempotent no-op (still returns the record)
        rec = self.get(uid)
        self._append({"kind": KIND_DEMOTE, "record_version": REGISTRY_RECORD_VERSION, "unit_id": uid,
                      "demoted_by": str(demoted_by), "reason": reason,
                      # deterministic: reuse the unit's own registered_at as the demote stamp (no clock).
                      "demoted_at": _compiled_at(rec["unit"]) if rec else ""})
        return self.get(uid)

    def mark_active(self, unit_id: str) -> dict:
        """Re-activate a previously-demoted unit (a manual rollback/activate), DEMOTING whatever is currently
        active for the same capability (so the single-active-per-capability invariant holds). Re-uses the
        register/demote event idiom: appends a fresh ``register`` event for the existing unit (idempotent on
        content, re-activating it) after demoting the current active one. Returns the now-active record."""
        uid = str(unit_id)
        rec = self.get(uid)
        if rec is None:
            raise RegistryError(f"cannot mark active unit {uid!r} — it was never registered")
        if uid in self._active_ids():
            return rec  # already active — no-op
        capability_id = str(rec["unit"][_CAP_ID])
        current = self.latest_active_for(capability_id)
        if current is not None:
            self._append({"kind": KIND_DEMOTE, "record_version": REGISTRY_RECORD_VERSION,
                          "unit_id": str(current[_UNIT_ID]), "demoted_by": uid,
                          "reason": "superseded by a re-activated (rolled-back-to) unit",
                          "demoted_at": _compiled_at(rec["unit"])})
        # re-register the SAME unit content (idempotent fold re-adds it to the active set); registered_at stays the
        # unit's own compiled_at so the action is deterministic + replayable.
        reactivate = {
            "kind": KIND_REGISTER, "record_version": REGISTRY_RECORD_VERSION, "unit": rec["unit"],
            "active": True, "registered_at": _compiled_at(rec["unit"]),
            "rollback_target": rec.get("rollback_target", ""), "supersedes": rec.get("supersedes", ""),
            "reactivated": True,
        }
        self._append(reactivate)
        return self.get(uid) or reactivate

    def rollback_to(self, capability_id: str) -> dict:
        """REAL rollback: re-activate the rollback target (the predecessor) of the capability's current active
        unit, demoting that current unit. Returns the now-active (rolled-back-to) record. Raises if there is no
        rollback target (a capability on its first compile has nothing to roll back to — HONEST, not a silent
        no-op)."""
        target = self.rollback_target(capability_id)
        if target is None:
            raise RegistryError(
                f"capability {capability_id!r} has no rollback target — it is on its first compiled unit "
                "(nothing to roll back to). The registry never fabricates a predecessor.")
        return self.mark_active(str(target[_UNIT_ID]))

    def _append(self, record: dict) -> None:
        """Append one event to the durable log AND refold (keep the projection in sync). The AppendLog write is the
        crash-safe commit; ``rebuild`` re-validates + recomputes state from the full log so the in-memory
        projection always equals a fresh rehydration."""
        self._log.append(record)
        self.rebuild()

    # ── read path (deterministic) ─────────────────────────────────────────────────────────────────────────────
    def get(self, unit_id: str) -> dict | None:
        """The current registry record for a unit_id (active flag reflects the latest fold), or None if unknown.
        The returned record's ``active`` is recomputed from the demote events so it is always current."""
        uid = str(unit_id)
        active = self._active_ids()
        for rec in self._unit_records():
            if str(rec["unit"][_UNIT_ID]) == uid:
                out = dict(rec)
                out["active"] = uid in active
                return out
        return None

    def history(self, capability_id: str) -> list[dict]:
        """EVERY compiled unit ever registered for a capability — active AND demoted (lossless: superseded units
        are preserved, not deleted) — in deterministic order ``(capability_version, compiled_at, unit_id)``. Each
        returned record carries a current ``active`` flag. This is the per-capability deploy_topology analog: the
        full version timeline of runtimes for one capability."""
        cap = str(capability_id)
        active = self._active_ids()
        out: list[dict] = []
        for rec in self._unit_records():
            if str(rec["unit"][_CAP_ID]) == cap:
                r = dict(rec)
                r["active"] = str(rec["unit"][_UNIT_ID]) in active
                out.append(r)
        out.sort(key=lambda r: _order_key(r["unit"]))
        return out

    def latest_for(self, capability_id: str) -> dict | None:
        """The NEWEST compiled unit for a capability by ``(capability_version, compiled_at, unit_id)``, regardless
        of active state (the highest version that was ever compiled). None if the capability has none. Use
        ``latest_active_for`` for the one that is currently the live runtime."""
        hist = self.history(capability_id)
        return hist[-1]["unit"] if hist else None

    def latest_active_for(self, capability_id: str) -> dict | None:
        """The currently-ACTIVE compiled unit for a capability (the live runtime). Exactly one active unit exists
        per capability under the register/demote invariant; if several somehow are active (a hand-edited log),
        the newest by order key wins. None when the capability has no active unit."""
        cap = str(capability_id)
        active = self._active_ids()
        actives = [rec["unit"] for rec in self._unit_records()
                   if str(rec["unit"][_CAP_ID]) == cap and str(rec["unit"][_UNIT_ID]) in active]
        if not actives:
            return None
        actives.sort(key=_order_key)
        return actives[-1]

    def rollback_target(self, capability_id: str) -> dict | None:
        """The unit to roll back TO for a capability = the predecessor of the current active unit (the prior
        promoted runtime). This makes the compiler's ``rollback_target`` field CONSUMABLE: the active unit names
        its predecessor's ``unit_id`` in ``rollback_target``; this returns that exact preserved unit.

        Returns None when there is no active unit, or the active unit has no predecessor (first compile). Raises
        ``RegistryIntegrityError`` if the active unit names a ``rollback_target`` that is not in the log — a
        tampered/missing-history failure that must be loud, not a silent wrong answer (HONEST)."""
        active = self.latest_active_for(capability_id)
        if active is None:
            return None
        target_id = active.get(_ROLLBACK_TARGET) or ""
        if not target_id:
            return None  # honestly: this is the first compiled unit — there is no predecessor
        rec = self.get(str(target_id))
        if rec is None:
            raise RegistryIntegrityError(
                f"capability {capability_id!r} active unit {active.get(_UNIT_ID)!r} names rollback_target "
                f"{target_id!r}, but that unit is NOT in the registry log — the history is tampered/missing. "
                "Refusing to return a rollback target the log cannot back (HONEST: fail, do not guess).")
        return rec["unit"]

    def list_active(self) -> list[dict]:
        """Every currently-ACTIVE compiled unit (one per capability with a live runtime), ordered by
        ``(capability_id, capability_version, compiled_at, unit_id)`` — deterministic. This IS the per-capability
        deploy_topology snapshot: the set of promoted capabilities that are now deployable/deployed runtimes."""
        active = self._active_ids()
        units = [rec["unit"] for rec in self._unit_records() if str(rec["unit"][_UNIT_ID]) in active]
        units.sort(key=lambda u: (str(u.get(_CAP_ID, "")), *_order_key(u)))
        return units

    def all_records(self) -> list[dict]:
        """Every register/demote event in the raw append-only log, in append order — the lossless audit trail
        (the demote events make supersession explicit). Read-only view for inspection/proofs."""
        return [dict(r) for r in self._records]

    def capability_ids(self) -> list[str]:
        """Every capability that has at least one registered unit, sorted (deterministic)."""
        return sorted({str(rec["unit"][_CAP_ID]) for rec in self._unit_records()})

    def close(self) -> None:
        self._log.close()


def open_registry(log_path: Path | str | None = None, *, db_path: Path | None = None) -> CompiledUnitRegistry:
    """Convenience constructor mirroring the repo's ``open(...)``-style factories (``_jsonl_store.open_log``)."""
    return CompiledUnitRegistry(log_path, db_path=db_path)


def register_units(units: Iterable[dict], log_path: Path | str | None = None) -> list[dict]:
    """Register a batch of compiled units into the registry at ``log_path`` (or the default), in order, returning
    the stored records. Convenience for the runtime's compile-on-promotion hook (register many at once)."""
    reg = open_registry(log_path)
    try:
        return [reg.register(u) for u in units]
    finally:
        reg.close()


__all__ = [
    "CompiledUnitRegistry", "open_registry", "register_units",
    "RegistryError", "RegistryIntegrityError",
    "REGISTRY_RECORD_VERSION", "KIND_REGISTER", "KIND_DEMOTE", "RECORD_KINDS",
    "DEFAULT_STATE_DIR", "DEFAULT_LOG_NAME",
]
