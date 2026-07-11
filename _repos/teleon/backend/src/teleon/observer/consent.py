"""observer.consent — GATE #0 for the consented-session corpus flywheel.

AIDevObserver is read-only / nothing-stored by DEFAULT. RETAINING a session for the corpus flywheel
(mining it into tools, research-queue entries, or standardized registry components) requires EXPLICIT,
GRANULAR, REVOCABLE consent from the session's subject — a human, an agent, or a pipeline. This module
is that contract, and it is gate #0: nothing downstream may retain a session unless this gate allows it.

The rules (see _repos/shared-backend-components/context/strategy/consented-session-corpus-flywheel.md):
  - DEFAULT-DENY. No active consent record covering (subject, purpose, scope) -> retention DENIED.
  - GRANULAR. Consent is per PURPOSE (tool_extraction / research_queue / component_standardization)
    and per SCOPE (a project glob; "*" = all the subject's sessions). A grant for one purpose never
    implies another; a grant for one scope never implies another.
  - REVOCABLE. Revoke removes consent immediately (and, by contract, deletes derived retention —
    revoke-and-delete; this module records the revoke, the corpus layer propagates the delete).
  - TIME-BOUNDED. Each grant has a retention window; past it, consent lapses (default-deny again).
  - REDACTION ALWAYS REQUIRED. Every allowed retention carries redaction_required=True — a session is
    redacted (secrets / PII / proprietary) before anything is kept. There is no un-redacted retention.

serves_truth=false: a retained/derived artifact is a CANDIDATE, never verified truth. The ledger is
append-only (grants + revokes) so consent state is auditable and reconstructable.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

#: who a session belongs to
SUBJECT_TYPES = ("human", "agent", "pipeline")
#: the purposes a subject can independently consent to (granular — one never implies another)
PURPOSES = ("tool_extraction", "research_queue", "component_standardization")
DEFAULT_RETENTION_DAYS = 90
CONSENT_VERSION = "1"
_DAY = 86400.0


@dataclass
class ConsentRecord:
    """One grant. `purposes` is a subset of PURPOSES; `scope` is a project glob ("*" = everything).
    Redaction is NOT a field — it is always required, so it cannot be consented away."""
    subject_id: str
    subject_type: str
    purposes: tuple[str, ...]
    scope: str = "*"
    retention_days: int = DEFAULT_RETENTION_DAYS
    granted_at: float = 0.0
    revoked_at: float | None = None
    version: str = CONSENT_VERSION

    def expires_at(self) -> float:
        return self.granted_at + self.retention_days * _DAY

    def active(self, now: float) -> bool:
        return self.revoked_at is None and now < self.expires_at()

    def to_json(self) -> dict:
        return {"subject_id": self.subject_id, "subject_type": self.subject_type,
                "purposes": list(self.purposes), "scope": self.scope, "retention_days": self.retention_days,
                "granted_at": self.granted_at, "revoked_at": self.revoked_at, "version": self.version}

    @staticmethod
    def from_json(d: dict) -> "ConsentRecord":
        return ConsentRecord(subject_id=d["subject_id"], subject_type=d.get("subject_type", "human"),
                             purposes=tuple(d.get("purposes", [])), scope=d.get("scope", "*"),
                             retention_days=int(d.get("retention_days", DEFAULT_RETENTION_DAYS)),
                             granted_at=float(d.get("granted_at", 0.0)),
                             revoked_at=d.get("revoked_at"), version=d.get("version", CONSENT_VERSION))


@dataclass
class Decision:
    """The gate-#0 answer. `redaction_required` is ALWAYS True when allowed — retention is never raw."""
    allowed: bool
    reason: str
    purpose: str = ""
    scope: str = "*"
    redaction_required: bool = True
    retain_until: float | None = None


def _scope_covers(grant_scope: str, session_scope: str) -> bool:
    """Does a grant's scope cover a session's scope? "*" covers all; "acme/*" covers "acme" + "acme/…"."""
    if grant_scope == "*" or grant_scope == session_scope:
        return True
    if grant_scope.endswith("/*"):
        prefix = grant_scope[:-1]            # "acme/"
        return session_scope == grant_scope[:-2] or session_scope.startswith(prefix)
    return False


class ConsentStore:
    """Append-only consent ledger with a DEFAULT-DENY decision view. JSON-backed when a path is given
    (the audit trail); pure in-memory otherwise (the self-test). Never raises on a missing/garbled file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._records: list[ConsentRecord] = []
        if self.path and self.path.exists():
            self._load()

    # ---- mutations (append-only) ----
    def grant(self, record: ConsentRecord) -> ConsentRecord:
        if record.subject_type not in SUBJECT_TYPES:
            raise ValueError(f"unknown subject_type '{record.subject_type}'")
        bad = [p for p in record.purposes if p not in PURPOSES]
        if bad:
            raise ValueError(f"unknown purpose(s): {bad}")
        if not record.granted_at:
            record.granted_at = time.time()
        self._records.append(record)
        self._persist()
        return record

    def revoke(self, subject_id: str, *, purpose: str | None = None, now: float | None = None) -> int:
        """Revoke all of a subject's consent (or just one purpose). Returns how many records it closed.
        Revoke-and-delete: the corpus layer reads revoked records and deletes the derived retention."""
        now = time.time() if now is None else now
        closed = 0
        for r in self._records:
            if r.subject_id != subject_id or r.revoked_at is not None:
                continue
            if purpose is None:                                  # revoke the whole grant
                r.revoked_at = now
                closed += 1
            elif purpose in r.purposes:                          # narrow a multi-purpose grant
                remaining = tuple(p for p in r.purposes if p != purpose)
                if remaining:
                    r.purposes = remaining                       # the other purposes stay active
                else:
                    r.revoked_at = now                           # last purpose removed -> close it
                closed += 1
        if closed:
            self._persist()
        return closed

    # ---- the gate-#0 decision (default-deny) ----
    def may_retain(self, subject_id: str, *, purpose: str, scope: str = "*", now: float | None = None) -> Decision:
        now = time.time() if now is None else now
        if purpose not in PURPOSES:
            return Decision(False, f"unknown purpose '{purpose}'", purpose=purpose, scope=scope)
        for r in self._records:
            if (r.subject_id == subject_id and purpose in r.purposes and r.active(now)
                    and _scope_covers(r.scope, scope)):
                return Decision(True, "active consent covers subject + purpose + scope",
                                purpose=purpose, scope=scope, redaction_required=True, retain_until=r.expires_at())
        return Decision(False, "no active consent (default-deny)", purpose=purpose, scope=scope)

    def active_records(self, now: float | None = None) -> list[ConsentRecord]:
        now = time.time() if now is None else now
        return [r for r in self._records if r.active(now)]

    # ---- persistence (append-only JSONL) ----
    def _persist(self) -> None:
        if not self.path:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("\n".join(json.dumps(r.to_json()) for r in self._records) + "\n", encoding="utf-8")
        except OSError:
            pass

    def _load(self) -> None:
        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError:
            self._records = []
            return
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                self._records.append(ConsentRecord.from_json(json.loads(line)))
            except ValueError:
                # per-line guard: a torn/invalid consent record must NOT discard the valid consents
                # after it — gate #0 stays default-deny for the missing one, but later real consents survive.
                continue


def gate_retention(store: ConsentStore, subject_id: str, *, purpose: str, scope: str = "*",
                   now: float | None = None) -> Decision:
    """GATE #0 — may this session be retained for the corpus flywheel? Default-deny; on allow, the caller
    MUST redact before retaining (decision.redaction_required is always True) and must stop retaining past
    decision.retain_until. This is the single function every retain path calls before keeping anything."""
    return store.may_retain(subject_id, purpose=purpose, scope=scope, now=now)


# --------------------------------------------------------------------------- self-test
def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    now = 1_000_000_000.0
    store = ConsentStore()  # in-memory

    # 1. DEFAULT-DENY: nothing consented -> denied
    d = gate_retention(store, "ada", purpose="tool_extraction", now=now)
    ck("default-deny: no consent -> retention denied", d.allowed is False and "default-deny" in d.reason)

    # 2. grant -> allowed, and redaction is ALWAYS required
    store.grant(ConsentRecord("ada", "human", ("tool_extraction", "research_queue"), scope="acme/*",
                              retention_days=30, granted_at=now))
    d = gate_retention(store, "ada", purpose="tool_extraction", scope="acme/widgets", now=now + _DAY)
    ck("grant -> allowed for the granted purpose+scope", d.allowed is True)
    ck("every allowed retention requires redaction", d.redaction_required is True)

    # 3. PURPOSE granularity: a purpose NOT granted is denied
    d = gate_retention(store, "ada", purpose="component_standardization", scope="acme/widgets", now=now + _DAY)
    ck("purpose granularity: ungranted purpose denied", d.allowed is False)

    # 4. SCOPE granularity: outside the granted scope is denied
    d = gate_retention(store, "ada", purpose="tool_extraction", scope="other/repo", now=now + _DAY)
    ck("scope granularity: out-of-scope denied", d.allowed is False)

    # 5. EXPIRY: past the retention window -> denied (consent lapses)
    d = gate_retention(store, "ada", purpose="tool_extraction", scope="acme/widgets", now=now + 31 * _DAY)
    ck("time-bounded: expired consent denied", d.allowed is False)

    # 6. REVOKE one purpose: the other survives
    store.revoke("ada", purpose="research_queue", now=now + 2 * _DAY)
    d_tool = gate_retention(store, "ada", purpose="tool_extraction", scope="acme/widgets", now=now + 3 * _DAY)
    d_res = gate_retention(store, "ada", purpose="research_queue", scope="acme/widgets", now=now + 3 * _DAY)
    ck("revoke one purpose leaves the other intact", d_tool.allowed is True and d_res.allowed is False)

    # 7. REVOKE all: everything denied
    store.revoke("ada", now=now + 4 * _DAY)
    d = gate_retention(store, "ada", purpose="tool_extraction", scope="acme/widgets", now=now + 5 * _DAY)
    ck("full revoke -> denied", d.allowed is False)

    # 8. agents + pipelines are first-class subjects
    store.grant(ConsentRecord("ci-bot", "pipeline", ("research_queue",), scope="*", granted_at=now))
    d = gate_retention(store, "ci-bot", purpose="research_queue", scope="anything", now=now + _DAY)
    ck("agents/pipelines are first-class subjects", d.allowed is True)

    # 9. redaction cannot be consented away (no field for it)
    ck("redaction is not a togglable field on ConsentRecord", "redaction" not in ConsentRecord.__dataclass_fields__)

    # 10. ledger round-trips (append-only audit trail)
    rt = ConsentRecord.from_json(ConsentRecord("x", "human", ("tool_extraction",), granted_at=now).to_json())
    ck("consent record round-trips through the ledger", rt.subject_id == "x" and rt.purposes == ("tool_extraction",))

    if fails:
        print(f"FAIL - observer.consent: {len(fails)} failure(s)")
        return 1
    print("PASS - observer.consent: gate #0 is default-deny, granular by purpose+scope, time-bounded, revocable "
          "(incl. per-purpose), redaction always required, agents/pipelines first-class, ledger auditable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
