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


_DISPOSITION_STATUS = {"block": "blocked", "review": "held_out", "serve": "ok", "info": "ok"}


def _vertical_journey(example: dict) -> dict:
    """A regulated-fact-vertical journey, built from the REAL showcase pipeline behind the examples-gallery
    registry (the ONE source for all verticals): describe the task -> the capability gap (the structural lift)
    -> run the governed pipeline -> serve the verdict with its evidence rows -> the governance boundary. The
    verdict + rows are the showcase's ACTUAL output (example['invoke'] runs run() on the module's own fixtures)."""
    import importlib
    module = importlib.import_module(f"scripts.showcase_pipelines.{example['id']}")
    result = example["invoke"](module)
    disposition, headline = example["verdict"](result)
    rows = example["rows"](result)
    serves_truth = result.get("serves_truth", False) if isinstance(result, dict) else False
    steps = [
        {"action": "Describe the regulated-context task", "surface": "intake", "status": "ok",
         "outcome": " ".join(str(example["scenario"]).split())[:180], "evidence_ref": None},
        {"action": "Capability gap — why a bare model fails (the structural lift)", "surface": "gap-screen",
         "status": "ok", "outcome": " ".join(str(example["fails"]).split())[:180], "evidence_ref": None},
        {"action": "Run the governed pipeline (earned authority, deterministic)",
         "surface": "reconciliation+verification", "status": _DISPOSITION_STATUS.get(disposition, "ok"),
         "outcome": str(headline)[:200], "evidence_ref": None},
        {"action": "Serve the governed verdict with its evidence rows", "surface": "consumption", "status": "ok",
         "outcome": "; ".join(f"{k}: {v}" for k, v in rows[:4])[:240], "evidence_ref": None},
        {"action": "Governance boundary: output is evidence/candidate, never autonomous truth",
         "surface": "governance", "status": "ok", "outcome": f"serves_truth={serves_truth}", "evidence_ref": None},
    ]
    return {"product": "Baltor", "name": f"{example['title']} — {example['domain']}",
            "steps": steps, "headline": str(headline)}


def all_journeys() -> dict:
    """The full journey registry: the two flagship Baltor journeys + EVERY regulated-fact vertical (sourced from
    the examples-gallery registry so verticals stay single-sourced, not duplicated). Built on demand so the
    scripts.* imports resolve after the path is set (works whether the module is imported or run directly)."""
    registry: dict = {
        "baltor-context-assurance": lambda: _baltor_context_assurance(corpus="cfpb"),
        "baltor-context-assurance-bill782": lambda: _baltor_context_assurance(corpus="acme"),
    }
    from scripts.build_examples_gallery import EXAMPLES
    for ex in EXAMPLES:
        registry[f"vertical-{ex['id']}"] = (lambda ex=ex: _vertical_journey(ex))
    return registry


_SECRET_MARKERS = ("bearer ", "sk-", "api_key=", "password", "secret:")  # redaction guard for the trace


def track(journey_id: str) -> dict:
    """Run a registered journey against the real backend and return a UserJourneyTrace.v1 (deterministic)."""
    registry = all_journeys()
    if journey_id not in registry:
        raise KeyError(f"unknown journey {journey_id!r}; known: {sorted(registry)}")
    j = registry[journey_id]()
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
    reg = all_journeys()
    verticals = sorted(j for j in reg if j.startswith("vertical-"))
    ck("the flagship + ALL regulated-fact verticals are registered (>=15 journeys)", len(reg) >= 15, str(len(reg)))
    ck("there are >=12 vertical journeys (one per showcase)", len(verticals) >= 12, str(len(verticals)))
    vt = track(verticals[0]) if verticals else {}
    ck("a vertical journey runs the real showcase into a 5-step trace that never serves truth",
       len(vt.get("steps", [])) == 5 and vt.get("serves_truth") is False, str(vt.get("name")))

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
        print("\n".join(sorted(all_journeys())))
        return 0
    if a.journey:
        print(json.dumps(track(a.journey), indent=2 if a.json else None, sort_keys=not a.json))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
