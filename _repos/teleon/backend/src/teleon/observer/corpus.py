"""observer.corpus — the consented-session corpus pipeline (stages 2-4 of the flywheel).

Gate #0 is observer.consent. THIS module is what runs AFTER consent says yes:
  - RETAIN (stage 2): redact a session, then keep it as a CANDIDATE retention record — but ONLY when
    consent.gate_retention allows it. No consent -> retain_session returns None (the default read-only,
    nothing-stored path is unchanged). Redaction is mandatory and runs before anything is kept.
  - MINE (stage 3): run the observer's own detectors (review_session) over a retained session and turn
    the findings into (a) COMPONENT candidates (capabilities that keep getting rebuilt -> standardize +
    register so future users don't reinvent) and (b) RESEARCH-QUEUE entries (gaps / patterns to look at).
  - STANDARDIZE (stage 4): shape a mined component candidate into a governed, registry-ready record —
    serves_truth=false, status=candidate, with provenance back to the consented session. It does NOT
    self-promote: the EXISTING ingest security gate (scripts/discovery_pipeline) scans it and the
    promotion boundary governs it. (Clean layering: this PRODUCT module never imports the dev-plane
    scripts; it emits candidates the dev-plane gates consume.)

Everything here is candidate-only (serves_truth=false), tenant-isolated by construction (a retention
record carries its subject; a tenant's private patterns never become global until consented + promoted),
and provenance-tracked. See _repos/shared-backend-components/context/strategy/consented-session-corpus-flywheel.md.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from .consent import ConsentStore, gate_retention
from .review import review_session

#: retention-redaction FLOOR — obvious secrets/PII stripped before a session is ever kept. This is the
#: corpus floor; the service layer's response_redaction is the fuller rail. Redact more, never less.
_REDACT_RE = re.compile(
    r"(sk-[A-Za-z0-9]{8,}|gsk_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12}|ghp_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|secret://[^\s\"']+|Bearer\s+[A-Za-z0-9._-]{12,}"
    r"|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"                       # emails
    r"|-----BEGIN[^-]*PRIVATE KEY-----)")
#: KEY=secret env-style assignments (redact the value, keep the key)
_ENV_RE = re.compile(r"(?i)\b([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)[A-Z0-9_]*)\s*=\s*([^\s\"']+)")


def redact_for_retention(text: str) -> tuple[str, int]:
    """Strip obvious secrets/PII. Returns (redacted_text, n_redactions). Mandatory before retention."""
    n = 0

    def _r(_m: re.Match) -> str:
        nonlocal n
        n += 1
        return "[REDACTED]"

    out = _ENV_RE.sub(lambda m: f"{m.group(1)}=[REDACTED]", text or "")
    n += len(_ENV_RE.findall(text or ""))
    out = _REDACT_RE.sub(_r, out)
    return out, n


def retain_session(store: ConsentStore, *, session_id: str, subject_id: str, subject_type: str,
                   purpose: str, scope: str, messages: list[dict], now: float | None = None) -> dict | None:
    """STAGE 2 + GATE #0: keep a redacted CANDIDATE retention of a session — only if consent allows it.
    Returns the retention record, or None when consent denies (nothing is kept; read-only path unchanged)."""
    decision = gate_retention(store, subject_id, purpose=purpose, scope=scope, now=now)
    if not decision.allowed:
        return None
    redactions = 0
    kept: list[dict] = []
    for m in messages:
        red, k = redact_for_retention(str(m.get("content", "")))
        redactions += k
        kept.append({"role": m.get("role", "user"), "content": red})
    return {
        "record": "retained_session", "session_id": session_id,
        "subject_id": subject_id, "subject_type": subject_type,
        "purpose": purpose, "scope": scope, "retain_until": decision.retain_until,
        "redactions": redactions, "messages": kept,
        "serves_truth": False, "consented": True,
        "provenance": {"source": "aidevobserver_session", "session_id": session_id,
                       "subject_id": subject_id, "consent_purpose": purpose},
    }


def mine_session(messages: list[dict]) -> dict:
    """STAGE 3: run the observer detectors over a session -> component candidates + research-queue entries.
    Reinvention findings (a capability rebuilt) become COMPONENT candidates; the rest become RESEARCH entries."""
    report = review_session(messages).get("report", [])
    components: list[dict] = []
    research: list[dict] = []
    for f in report:
        ftype = str(f.get("type", ""))
        if ftype.startswith("reinvention"):
            components.append({
                "capability": (f.get("suggestion") or f.get("message") or "")[:200],
                "evidence": f.get("evidence", ""), "source_ref": f.get("source_ref"),
                "confidence": f.get("confidence", 0.0),
                # no source_ref => not yet covered in the federation => a genuine gap worth standardizing
                "covered": bool(f.get("source_ref")),
            })
        else:
            research.append({"area": ftype, "note": (f.get("message") or "")[:200],
                             "confidence": f.get("confidence", 0.0)})
    return {"components": components, "research": research}


def standardize_candidate(candidate: dict, *, subject_id: str, session_id: str = "") -> dict:
    """STAGE 4: shape a mined component candidate into a governed, REGISTRY-READY record. serves_truth=false,
    status=candidate, provenance to the consented session. Does NOT self-promote — the ingest security gate
    scans it and the promotion boundary governs tenant-visibility."""
    cap = str(candidate.get("capability", "")).strip()
    slug = re.sub(r"[^a-z0-9]+", "_", cap.lower()).strip("_")[:48] or "component"
    return {
        "id": f"consented_{slug}",
        "name": cap or "standardized component",
        "kind": "standardized_primitive",
        "from_reinvention": True, "already_covered": bool(candidate.get("covered")),
        "evidence": candidate.get("evidence", ""),
        "status": "candidate", "serves_truth": False,
        "provenance": {"origin": "consented_session_mining", "subject_id": subject_id,
                       "session_id": session_id, "source_ref": candidate.get("source_ref")},
    }


# --------------------------------------------------------------------------- self-test
def _self_test() -> int:
    from .consent import ConsentRecord
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    now = 1_000_000_000.0
    session = [
        {"role": "user", "content": "let me write a csv parser from scratch; my key is sk-ABCDEF1234567890"},
        {"role": "assistant", "content": "creating parse_csv(); export TOKEN_SECRET=hunter2abcdef email me at a@b.com"},
    ]

    # GATE #0: no consent -> nothing retained
    store = ConsentStore()
    ck("no consent -> retain_session returns None (nothing kept)",
       retain_session(store, session_id="s1", subject_id="ada", subject_type="human",
                      purpose="tool_extraction", scope="acme/x", messages=session, now=now) is None)

    # consent granted -> retained, and secrets are REDACTED before keeping
    store.grant(ConsentRecord("ada", "human", ("tool_extraction", "research_queue", "component_standardization"),
                              scope="acme/*", retention_days=30, granted_at=now))
    rec = retain_session(store, session_id="s1", subject_id="ada", subject_type="human",
                         purpose="tool_extraction", scope="acme/x", messages=session, now=now + 1)
    blob = " ".join(m["content"] for m in rec["messages"]) if rec else ""
    ck("consent -> session retained as a candidate", rec is not None and rec["serves_truth"] is False)
    ck("secrets/PII redacted before retention", rec is not None and "sk-ABCD" not in blob
       and "hunter2abcdef" not in blob and "a@b.com" not in blob and rec["redactions"] >= 3)
    ck("retention carries provenance to the consented session", rec["provenance"]["session_id"] == "s1")

    # MINE: a reinvention session yields a component candidate
    mined = mine_session(session)
    ck("mining a reinvention session yields a component candidate", len(mined["components"]) >= 1)

    # STANDARDIZE: a candidate becomes a governed, registry-ready record (not auto-promoted)
    comp = mined["components"][0] if mined["components"] else {"capability": "csv reader", "covered": False}
    std = standardize_candidate(comp, subject_id="ada", session_id="s1")
    ck("standardized record is governed (candidate, serves_truth=false, provenance)",
       std["status"] == "candidate" and std["serves_truth"] is False and std["provenance"]["subject_id"] == "ada")
    ck("standardized record does NOT self-promote (no truth_authority/promoted flag)",
       "promoted" not in std and std.get("serves_truth") is False)

    if fails:
        print(f"FAIL - observer.corpus: {len(fails)} failure(s)")
        return 1
    print("PASS - observer.corpus: consent-gated retain (deny->None), mandatory redaction, detector-driven "
          "mining (components + research), governed standardize (candidate-only, provenance, no self-promote).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
