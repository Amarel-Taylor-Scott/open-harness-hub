#!/usr/bin/env python3
"""check_teleon_distillation — proof for the distiller + the meta-learner (distill cheaper/faster, and learn to).

DISTILLER — turns an unbounded capability into a DETERMINISTIC FORK on its evolution graph + a DistillationRecord:
  * a determinism-ceiling ~1.0 capability (a pure API/compute call) distills to a fully-deterministic rule that
    covers ~all cases at ~zero per-call cost, via the cheap direct_api_rule strategy, verified equivalent on the
    covered cases; the model parent is PRESERVED and the residual routed to it (lossless).
  * a low-ceiling capability distills only its deterministic sliver (residual stays on the model) — still lossless.
  * the fork stays WITHIN CONFINES: it is checked against the org guardrail policy (a deterministic rule is exactly
    what a strict org wants, so it is applied).
META-LEARNER — learns the cheapest-effective strategy + lane per capability class from the records:
  * cold start -> the prior; with evidence -> the highest determinism/coverage-saving-per-distill-cost strategy,
    which can OVERRIDE the prior; recommends the cheapest inference lane proven sufficient for the class; the
    learned choice is deterministic and the efficiency summary shows distill cost SAVED (the moat metric).

CLI: python3 scripts/check_teleon_distillation.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import DistillationMetaLearner, choose_strategy, distill
from src.teleon.governance import load_policy


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── DISTILLER: a determinism-ceiling 1.0 capability -> a fully-deterministic, ~zero-cost rule. ──
    d = distill("live-stock-price-quote", category="financial-data", determinism_ceiling=1.0,
                deterministic_coverage_estimate=1.0)
    rec = d["record"]
    ck("ceiling-1.0 distills via the cheap direct_api_rule strategy", rec["strategy"] == "direct_api_rule")
    ck("the deterministic fork covers ~all cases at ~zero per-call cost (cost 0.07 -> 0.0)",
       rec["coverage"] == 1.0 and rec["per_call_cost_after"] == 0.0 and rec["per_call_cost_before"] > 0)
    ck("the covered cases are verified equivalent to the model (a pure deterministic call)",
       rec["equivalence_verified"] is True)
    ck("the distillation is lossless (parent preserved + residual routed) and never serves truth",
       rec["lossless"] is True and d["serves_truth"] is False
       and any(r["kind"] == "model" for r in d["graph"]["runners"]))
    ck("the graph descent walks model -> deterministic rule",
       [n.split("::")[-1] for n in d["graph"]["descent_path"]] == ["model@v1", "deterministic@distilled"])

    # MODEL DOWNGRADE: an open-ended/text capability that CANNOT go deterministic descends to a CHEAPER model
    # (the efficiency win — cost/latency/llm_usage improve; determinism does NOT). residual -> the frontier model.
    ck("a low determinism-ceiling defaults to the model_downgrade strategy", choose_strategy(0.25) == "model_downgrade")
    low_full = distill("autonomous-research-agent", category="research", determinism_ceiling=0.25,
                       deterministic_coverage_estimate=0.35)
    low = low_full["record"]
    ck("model_downgrade forks to a CHEAPER MODEL (still non-deterministic), not a deterministic rule",
       low["strategy"] == "model_downgrade" and low["fork_runner_id"].endswith("::cheaper_model@distilled")
       and any(r["kind"] == "cheaper_model" for r in low_full["graph"]["runners"]))
    ck("it is a COST win (cheaper than frontier) but NOT free and NOT deterministic (determinism unchanged)",
       0 < low["per_call_cost_after"] < low["per_call_cost_before"] and low["equivalence_verified"] is False
       and any(r["kind"] == "cheaper_model" and r["determinism"] < 1.0 for r in low_full["graph"]["runners"]))
    ck("the improvement axes are cost/latency/llm_usage (cheaper, faster, lower-context) — NOT determinism",
       set(low["improvement_axes"]) == {"cost", "latency", "llm_usage"} and low["lossless"] is True
       and low["residual_fraction"] > 0.5)
    ck("a deterministic strategy improves determinism TOO (the other descent axis)",
       "determinism" in distill("xbrl", category="financial-data", determinism_ceiling=1.0,
                                 deterministic_coverage_estimate=1.0)["record"]["improvement_axes"])
    # GOVERNANCE: a deterministic-only org will NOT accept a cheaper-model fork (still non-deterministic) -> held.
    audit0 = load_policy("deterministic-audit")
    held = distill("open-ended-writer", category="other", determinism_ceiling=0.25,
                   deterministic_coverage_estimate=0.4, policy=audit0)
    ck("under a deterministic-only org, a cheaper-model fork is HELD (it is not deterministic) — escalate",
       held["applied"] is False and held["record"]["policy_allowed"] is False)

    # WITHIN CONFINES: the deterministic fork is what a strict org wants -> applied under deterministic-audit.
    audit = load_policy("deterministic-audit")
    da = distill("ecfr-regulation-lookup", category="regulation", determinism_ceiling=0.9,
                 deterministic_coverage_estimate=0.85, policy=audit)
    ck("under a deterministic-only org, the distilled rule stays within confines and is APPLIED",
       da["applied"] is True and da["record"]["policy_allowed"] is True)

    # ── META-LEARNER: cold start -> prior; evidence -> learned (can override the prior). ──
    ml = DistillationMetaLearner()
    ck("cold start recommends the prior strategy", ml.recommend_strategy("scraping", 0.8)["source"] == "prior"
       and ml.recommend_strategy("scraping", 0.8)["strategy"] == choose_strategy(0.8))

    # For the 'scraping|extract' class, feed evidence that the CHEAP template_match matches coverage at lower cost
    # than the prior deterministic_extract -> the learner should OVERRIDE the prior to the higher-efficiency strategy.
    def mkrec(strategy, distill_cost, coverage=0.9):
        return {"capability_slot": "s", "category": "scraping", "strategy": strategy, "determinism_ceiling": 0.8,
                "per_call_cost_before": 0.07, "per_call_cost_after": 0.0, "distill_cost": distill_cost,
                "coverage": coverage, "residual_fraction": round(1 - coverage, 6), "equivalence_verified": False,
                "lossless": True, "policy_allowed": True, "applied": True, "fork_runner_id": "s::deterministic"}
    for _ in range(3):
        ml.record(mkrec("deterministic_extract", 0.18))
    for _ in range(3):
        ml.record(mkrec("template_match", 0.08))  # same coverage, cheaper -> higher efficiency
    learned = ml.recommend_strategy("scraping", 0.8)
    ck("with evidence, the learner recommends the cheapest-effective strategy (LEARNED, overriding the prior)",
       learned["source"] == "learned" and learned["strategy"] == "template_match"
       and learned["strategy"] != choose_strategy(0.8), str(learned))
    ck("the learned recommendation is deterministic",
       ml.recommend_strategy("scraping", 0.8) == learned)

    # recommend the cheapest LANE proven sufficient for a class (run distillation on the cheapest sufficient model).
    ml.record(mkrec("template_match", 0.08), lane_id="model.openai.codex@candidate", lane_cost=0.02)
    ml.record(mkrec("template_match", 0.08), lane_id="model.ollama_local@candidate", lane_cost=0.0)
    lane = ml.recommend_lane("scraping", 0.8)
    ck("the learner recommends the cheapest inference lane that succeeded (local Ollama over Codex)",
       lane["source"] == "learned" and lane["lane_id"] == "model.ollama_local@candidate", str(lane))

    # the moat metric: a learned class + distill cost saved by choosing the best strategy over the worst.
    summary = ml.efficiency_summary()
    ck("the efficiency summary reports learned classes + distill cost SAVED vs the worst strategy (the moat metric)",
       summary["classes_learned"] >= 1 and summary["distill_cost_saved_vs_worst"] > 0, str(summary))

    # fail loud on a malformed record.
    raised = False
    try:
        ml.record({"strategy": "x"})  # no category
    except ValueError:
        raised = True
    ck("a record with no category/strategy fails loud", raised)

    print("\n" + ("PASS - check_teleon_distillation: the distiller turns a capability into a deterministic fork "
                  "(ceiling-1.0 -> a fully-deterministic ~zero-cost rule, equivalence-verified, lossless, within "
                  "the org's confines); the meta-learner learns from the records the cheapest-effective distillation "
                  "STRATEGY per class (overriding the prior with evidence) and the cheapest sufficient LANE, and "
                  "reports the distill cost saved — distilling that gets cheaper as it runs. Deterministic, never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
