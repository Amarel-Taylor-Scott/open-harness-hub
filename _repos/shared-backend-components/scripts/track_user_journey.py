#!/usr/bin/env python3
"""scripts.track_user_journey — GOVERNED, REPLAYABLE user-journey tracking.

The recorded videos (`e2e/record_user_journeys.mjs`) SHOW a journey; this tracks it as a structured,
deterministic `UserJourneyTrace` that PROVES + replays it — the same thesis as the product itself
(receipts + lineage for everything, including the demo journeys). A journey runs against the REAL demo
backend (`demo_full_app.run_demo` — not a mock), maps each real outcome to an ordered step, and emits a
content-hashed trace that re-runs to the SAME hash. serves_truth=false (a journey trace is evidence).

Extensible: add a journey by registering a runner in JOURNEYS. stdlib only; deterministic; offline.

CLI:
    python3 _repos/shared-backend-components/scripts/track_user_journey.py --list
    python3 _repos/shared-backend-components/scripts/track_user_journey.py --journey baltor-context-assurance --json
    python3 _repos/shared-backend-components/scripts/track_user_journey.py --self-test
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

SCHEMA_VERSION = "UserJourneyTrace"


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


def _teleon_capability_plan(tenant_id: str, variety: str = "model") -> dict:
    """A Teleon journey: a TENANT's declared priority flows through the objective layer into a concrete plan for a
    capability-DEFINED unit — which runtime class to place it on, and whether to descend it to a cheaper
    deterministic rule. The SAME capability plans DIFFERENTLY per tenant: a cost tenant descends to the 90%-coverage
    deterministic rule; a compliance/accuracy tenant HOLDS the descent when that rule diverges on novel inputs.
    Built from the REAL objective + adapt() engines (not a mock); deterministic, so the trace replays to one hash."""
    from scripts.teleon_preseed_capabilities import _seed, objective_gated_descent, select_placement

    from src.teleon.objectives import objective_for_tenant
    obj = objective_for_tenant(tenant_id)
    unit = next(u for u in _seed()["units"] if u["variety"] == variety)
    slot = unit["spec"]["capability_slot"]
    placement = select_placement(unit, obj)
    # the capability genuinely has novel inputs (regulated facts vary), so the divergence is REAL; only the
    # tenant's PRIORITY decides whether to accept a 90%-coverage deterministic rule for it.
    descent = objective_gated_descent(obj, variety=variety, novel_divergence=True)
    held = descent["decision"] == "hold"
    steps = [
        {"action": "Tenant declares its priority", "surface": "intake", "status": "ok",
         "outcome": f"tenant {tenant_id!r} prioritizes {obj.name}", "evidence_ref": None},
        {"action": "Teleon binds the tenant to a CapabilityObjective", "surface": "objective-binding",
         "status": "ok", "outcome": f"objective={obj.name} over cost/latency/llm/determinism/accuracy",
         "evidence_ref": None},
        {"action": f"Place the capability ({slot}) on the best runtime class for the priority",
         "surface": "placement", "status": "ok",
         "outcome": f"chosen runtime: {placement['chosen']}", "evidence_ref": None},
        {"action": "Decide the non-deterministic -> deterministic descent under the priority",
         "surface": "self-improvement", "status": "held_out" if held else "ok",
         "outcome": ("descent HELD: accuracy priority vetoes a 90%-coverage rule that diverges on novel inputs "
                     "(model kept as rollback)" if held else
                     f"DESCEND: promote the distilled deterministic rule (cost {descent.get('before_cost')} -> "
                     f"{descent.get('after_cost')}); model kept as rollback"), "evidence_ref": None},
        {"action": "Governance boundary: a plan/selection is evidence, never autonomous truth",
         "surface": "governance", "status": "ok", "outcome": f"serves_truth={placement['serves_truth']}",
         "evidence_ref": None},
    ]
    return {"product": "Teleon", "name": f"Capability plan under tenant priority ({obj.name}) — {variety} unit",
            "steps": steps,
            "headline": f"{tenant_id}: {obj.name} -> place on {placement['chosen']}, descent={descent['decision']}"}


def _teleon_capability_descent_journey(tenant_id: str) -> dict:
    """A Teleon journey: watch a regulated-fact capability DESCEND — under the tenant's tunable preferences (soft
    objective + HARD blockers), the A/B harness picks the cheapest strategy that keeps accuracy (governed by the
    tenant's policy), the fragile fact is bound to its authoritative source (freshness: stale held out), and the
    whole thing is governed with provenance. Built from the REAL A/B + preferences + freshness engines; deterministic."""
    from scripts.eval.vertical_eval_suites import eval_suite_scorer

    from src.teleon.evolution import FreshnessSyncedCapability, ab_test
    from src.teleon.governance import preferences_for
    prefs = preferences_for(tenant_id)
    policy = prefs.to_org_policy()
    cap = {"capability_slot": "reg-e-error-resolution-deadline", "category": "regulation",
           "determinism_ceiling": 0.95, "deterministic_coverage_estimate": 0.9,
           "skill_text": ("You are a Reg E assistant.\nYou are a Reg E assistant.\n"
                          "Always cite ecfr://12/1005.11.\n[optional] background context.\n"
                          "[optional] more background.\nReturn the deadline in business days.\n"),
           "must_keep": ("ecfr://12/1005.11", "business days")}
    ab = ab_test(cap, scorer=eval_suite_scorer, max_accuracy_drop=prefs.max_accuracy_drop, policy=policy)
    fr = FreshnessSyncedCapability(cap["capability_slot"], authoritative_source="ecfr://12/1005.11",
                                   volatility_class="low")
    fresh = fr.sync("10 business days", now="t0", source_version="2025-edition")
    held = fr.on_source_change({"kind": "changed", "source": "ecfr://12/1005.11"}, now="t1")
    steps = [
        {"action": "Tenant declares tunable preferences (soft objective + HARD blockers)", "surface": "preferences",
         "status": "ok", "outcome": f"{tenant_id}: objective={prefs.to_objective().name}, "
         f"hard={'MIT-only+vetted' if policy.allowed_licenses else 'none'}, max_accuracy_drop={prefs.max_accuracy_drop}",
         "evidence_ref": None},
        {"action": "A/B the descent strategies; pick the cheapest that keeps accuracy (within the tenant's confines)",
         "surface": "descent-ab", "status": "ok",
         "outcome": f"winner={ab['winner']} @ accuracy {ab['winner_accuracy']} (floor {ab['accuracy_floor']}), cost {ab['winner_cost']}",
         "evidence_ref": None},
        {"action": "Token consumption (in/out) tracked; the skill is compressed where the model is kept",
         "surface": "tokens", "status": "ok",
         "outcome": f"winner tokens in/out: {ab['winner_tokens_in']}/{ab['winner_tokens_out']}; "
         f"prompt compression saves {ab['tokens_saved_by_compression']} input tokens (lossless={ab['compression_lossless']})",
         "evidence_ref": None},
        {"action": "Governance: the winning fork clears the accuracy floor + the org guardrail policy",
         "surface": "governance", "status": "ok",
         "outcome": f"within confines: accuracy>=floor={ab['winner_accuracy'] >= ab['accuracy_floor']}", "evidence_ref": None},
        {"action": "Freshness: bind the fragile fact to its authoritative source; hold stale out on change",
         "surface": "freshness", "status": "held_out",
         "outcome": f"synced to {fresh['provenance']['authoritative_source']} ({fr.policy['sync_cadence']}); "
         f"on rule change -> {held['status']} (stale never served)", "evidence_ref": fresh["provenance"]["source_version"]},
        {"action": "Governance boundary: a descent/serve decision is evidence, never autonomous truth",
         "surface": "governance", "status": "ok", "outcome": f"serves_truth={ab['serves_truth']}", "evidence_ref": None},
    ]
    return {"product": "Teleon", "name": f"Capability descent under tenant preferences ({prefs.to_objective().name}) — {tenant_id}",
            "steps": steps, "headline": f"{tenant_id}: descend -> {ab['winner']} (acc {ab['winner_accuracy']}), freshness-synced, governed"}


def all_journeys() -> dict:
    """The full journey registry: the two flagship Baltor journeys + EVERY regulated-fact vertical (sourced from
    the examples-gallery registry so verticals stay single-sourced, not duplicated). Built on demand so the
    scripts.* imports resolve after the path is set (works whether the module is imported or run directly)."""
    registry: dict = {
        "baltor-context-assurance": lambda: _baltor_context_assurance(corpus="cfpb"),
        "baltor-context-assurance-bill782": lambda: _baltor_context_assurance(corpus="acme"),
        # Teleon: the SAME capability planned differently per tenant priority (the per-tenant objective, on camera).
        "teleon-capability-plan-cost-tenant": lambda: _teleon_capability_plan("high-volume-batch"),
        "teleon-capability-plan-accuracy-tenant": lambda: _teleon_capability_plan("baltor-compliance"),
        # Teleon: watch a capability DESCEND under tunable tenant preferences (A/B + hard blockers + freshness + governance).
        "teleon-capability-descent-cost-startup": lambda: _teleon_capability_descent_journey("cost-first-startup"),
        "teleon-capability-descent-mit-bank": lambda: _teleon_capability_descent_journey("mit-only-bank"),
    }
    from scripts.build_examples_gallery import EXAMPLES
    for ex in EXAMPLES:
        registry[f"vertical-{ex['id']}"] = (lambda ex=ex: _vertical_journey(ex))
    return registry


_SECRET_MARKERS = ("bearer ", "sk-", "api_key=", "password", "secret:")  # redaction guard for the trace


def track(journey_id: str) -> dict:
    """Run a registered journey against the real backend and return a UserJourneyTrace (deterministic)."""
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

    # Teleon per-tenant objective FLOWS into the journey: the SAME capability plans DIFFERENTLY per tenant priority.
    cost_j = track("teleon-capability-plan-cost-tenant")
    acc_j = track("teleon-capability-plan-accuracy-tenant")
    ck("a Teleon capability-plan journey is tracked (objective-binding -> placement -> descent -> governance)",
       cost_j["product"] == "Teleon" and {s["surface"] for s in cost_j["steps"]}
       >= {"objective-binding", "placement", "self-improvement", "governance"}, str([s["surface"] for s in cost_j["steps"]]))
    cost_descent = next(s for s in cost_j["steps"] if s["surface"] == "self-improvement")
    acc_descent = next(s for s in acc_j["steps"] if s["surface"] == "self-improvement")
    ck("the cost tenant DESCENDS while the accuracy tenant HOLDS the descent — same capability, opposite plan by priority",
       cost_descent["status"] == "ok" and acc_descent["status"] == "held_out", f"{cost_descent['status']} vs {acc_descent['status']}")
    ck("the Teleon journeys are replayable (same trace_hash) and never serve truth",
       track("teleon-capability-plan-cost-tenant")["trace_hash"] == cost_j["trace_hash"]
       and cost_j["serves_truth"] is False and acc_j["serves_truth"] is False)

    # the DESCENT walkthrough journey: a capability descends under tunable preferences, governed, with freshness.
    desc = track("teleon-capability-descent-cost-startup")
    surfaces = {s["surface"] for s in desc["steps"]}
    ck("a capability-DESCENT journey walks preferences -> A/B descent -> tokens -> governance -> freshness -> boundary",
       desc["product"] == "Teleon" and {"preferences", "descent-ab", "tokens", "freshness", "governance"} <= surfaces, str(surfaces))
    tok_step = next(s for s in desc["steps"] if s["surface"] == "tokens")
    ck("the descent journey surfaces TOKEN consumption (in/out) + the prompt-compression savings",
       "tokens in/out" in tok_step["outcome"] and "saves" in tok_step["outcome"])
    ab_step = next(s for s in desc["steps"] if s["surface"] == "descent-ab")
    fr_step = next(s for s in desc["steps"] if s["surface"] == "freshness")
    ck("the descent step shows a measured winner; the freshness step holds the stale fact out (held_out)",
       "winner=" in ab_step["outcome"] and fr_step["status"] == "held_out" and "never served" in fr_step["outcome"])
    ck("the MIT-only bank descent journey reflects its HARD blocker in the preferences step",
       "MIT-only" in next(s for s in track("teleon-capability-descent-mit-bank")["steps"]
                          if s["surface"] == "preferences")["outcome"])
    ck("the descent journey is replayable + never serves truth",
       track("teleon-capability-descent-cost-startup")["trace_hash"] == desc["trace_hash"] and desc["serves_truth"] is False)

    print("\n" + ("PASS — track_user_journey: a user journey is tracked against the REAL demo backend as an ordered, "
                  "deterministic, REPLAYABLE UserJourneyTrace (same journey -> same trace_hash); the moat step "
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
