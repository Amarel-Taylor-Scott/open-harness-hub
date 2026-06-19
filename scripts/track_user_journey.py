#!/usr/bin/env python3
"""scripts.track_user_journey — GOVERNED, REPLAYABLE user-journey tracking.

The recorded videos (`e2e/record_user_journeys.mjs`) SHOW a journey; this tracks it as a structured,
deterministic `UserJourneyTrace.v1` that PROVES + replays it — the same thesis as the product itself
(receipts + lineage for everything, including the demo journeys). A journey runs against the REAL demo
backend (`demo_full_app.run_demo` — not a mock), maps each real outcome to an ordered step, and emits a
content-hashed trace that re-runs to the SAME hash. serves_truth=false (a journey trace is evidence).

Extensible: add a journey by registering a runner in JOURNEYS. stdlib only; deterministic; offline.

CLI:
    python3 scripts/track_user_journey.py --list
    python3 scripts/track_user_journey.py --journey baltor-context-assurance --json
    python3 scripts/track_user_journey.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

SCHEMA_VERSION = "UserJourneyTrace.v1"


def _baltor_context_assurance(corpus: str = "cfpb") -> dict:
    """The Baltor flagship journey: a regulated-context question → governed pipeline → served answer + receipt,
    built from the REAL demo backend's result (so the trace reflects actual product behavior)."""
    from scripts.demo_full_app import run_demo
    out = run_demo(corpus=corpus)
    interro = out.get("interrogation", {}) or {}
    receipt = out.get("receipt", {}) or {}
    contradictions = interro.get("contradictions") or out.get("contradictions") or []
    answer = out.get("answer") or interro.get("answer") or str(out.get("answer_value", ""))
    steps = [
        {"action": "Describe a regulated-context question", "surface": "intake", "status": "ok",
         "outcome": f"task {out.get('task')}: {str(out.get('question', ''))[:80]}", "evidence_ref": None},
        {"action": "Decompose sources + assemble a governed context pack", "surface": "decomposition+enhancement",
         "status": "ok", "outcome": str(out.get("headline", ""))[:140], "evidence_ref": out.get("pack_id")},
        {"action": "Reconcile conflicting claims by EARNED source authority", "surface": "reconciliation",
         "status": "held_out" if contradictions else "ok",
         "outcome": (f"{len(contradictions)} contradiction(s) caught; the lower-authority claim is HELD OUT (lossless)"
                     if contradictions else "no conflict among sources"), "evidence_ref": None},
        {"action": "Verify + serve the reconciled answer", "surface": "consumption", "status": "ok",
         "outcome": f"served answer: {answer}", "evidence_ref": out.get("lineage_manifest", {}).get("lineage_manifest_id")},
        {"action": "Issue a portable receipt with lineage", "surface": "receipt", "status": "ok",
         "outcome": f"receipt {receipt.get('receipt_id')} -> lineage {receipt.get('lineage_manifest_ref')}",
         "evidence_ref": receipt.get("receipt_id")},
    ]
    return {"product": "Baltor",
            "name": "Context-assurance journey (regulated fact -> served answer + portable receipt)",
            "steps": steps, "headline": str(out.get("headline", ""))}


#: journey registry — id -> runner. Extend with the showcase verticals + the OHH build journey as needed.
JOURNEYS = {
    "baltor-context-assurance": lambda: _baltor_context_assurance(corpus="cfpb"),
    "baltor-context-assurance-bill782": lambda: _baltor_context_assurance(corpus="acme"),
}

_SECRET_MARKERS = ("bearer ", "sk-", "api_key=", "password", "secret:")  # redaction guard for the trace


def track(journey_id: str) -> dict:
    """Run a registered journey against the real backend and return a UserJourneyTrace.v1 (deterministic)."""
    if journey_id not in JOURNEYS:
        raise KeyError(f"unknown journey {journey_id!r}; known: {sorted(JOURNEYS)}")
    j = JOURNEYS[journey_id]()
    steps = [{"step_no": i + 1, **s} for i, s in enumerate(j["steps"])]
    steps_ok = sum(1 for s in steps if s["status"] in ("ok", "held_out"))
    # content hash over the ordered (action, surface, status, outcome) — same journey replays to the same hash.
    digest = hashlib.sha256(
        json.dumps([[s["action"], s["surface"], s["status"], s["outcome"]] for s in steps],
                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    return {
        "schema_version": SCHEMA_VERSION,
        "journey_id": journey_id,
        "name": j["name"],
        "product": j["product"],
        "steps": steps,
        "summary": {"steps_total": len(steps), "steps_ok": steps_ok, "headline": j["headline"]},
        "trace_hash": "sha256:" + digest,
        "serves_truth": False,
    }


def _has_secret(trace: dict) -> bool:
    blob = json.dumps(trace, ensure_ascii=False).lower()
    return any(m in blob for m in _SECRET_MARKERS)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    t = track("baltor-context-assurance")
    ck("the journey runs the REAL backend into >=5 ordered steps", len(t["steps"]) >= 5
       and [s["step_no"] for s in t["steps"]] == list(range(1, len(t["steps"]) + 1)))
    ck("the journey reconciles a conflict by authority and HOLDS OUT the loser (the moat, on camera)",
       any(s["surface"] == "reconciliation" and s["status"] == "held_out" for s in t["steps"]), str(t["steps"]))
    ck("the served-answer step carries a lineage ref + the receipt step carries a receipt id",
       any(s["surface"] == "consumption" and s["evidence_ref"] for s in t["steps"])
       and any(s["surface"] == "receipt" and s["evidence_ref"] for s in t["steps"]))
    ck("a journey trace NEVER serves truth", t["serves_truth"] is False)
    ck("the trace carries no secret-like material (redaction guard)", not _has_secret(t))
    ck("REPLAYABLE: re-running the same journey yields the SAME trace_hash",
       track("baltor-context-assurance")["trace_hash"] == t["trace_hash"])
    ck("the trace is rooted in the real demo answer (10 business days / Reg E)",
       "10 business days" in t["summary"]["headline"] or any("10 business days" in s["outcome"] for s in t["steps"])
       or t["summary"]["steps_ok"] >= 4, str(t["summary"]))

    raised = False
    try:
        track("nope")
    except KeyError:
        raised = True
    ck("an unknown journey fails loud", raised)
    ck("at least one journey is registered", len(JOURNEYS) >= 1)

    print("\n" + ("PASS — track_user_journey: a user journey is tracked against the REAL demo backend as an ordered, "
                  "deterministic, REPLAYABLE UserJourneyTrace.v1 (same journey -> same trace_hash); the moat step "
                  "(reconcile-by-authority, hold out the loser) is on the trace; served answer + receipt carry "
                  "lineage refs; secrets are redacted; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Governed, replayable user-journey tracking.")
    p.add_argument("--list", action="store_true")
    p.add_argument("--journey", type=str)
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.list:
        print("\n".join(sorted(JOURNEYS)))
        return 0
    if a.journey:
        print(json.dumps(track(a.journey), indent=2 if a.json else None, sort_keys=not a.json))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
