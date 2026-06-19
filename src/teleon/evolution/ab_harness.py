"""src.teleon.evolution.ab_harness — A/B the descent STRATEGIES per capability, pick the measured winner, and
feed the meta-learner real evidence. This is what makes "we learn the most efficient path" MEASURED, not assumed.

The rule: descend as FAR as possible (cheapest / most-deterministic) WITHOUT regressing accuracy beyond a
tolerance vs the full-model baseline. For a capability it scores each candidate strategy against a benchmark
``scorer``, keeps only the org-policy-allowed strategies that stay within the accuracy tolerance, and picks the
cheapest survivor — so a cheap-but-WRONG fork is never shipped, and where the ceiling-only PRIOR would have
regressed accuracy, the A/B harness catches it (an accuracy regression prevented). The winning records feed the
meta-learner, which then recommends the measured-best strategy per capability class — turning the cold-start lift
(0.0, every fork used the prior) into evidence.

Composes distiller (build forks) + scorer/benchmark (measure accuracy) + org policy (bound) + meta_learner
(learn). Pure + deterministic (the scorer is injected; defaults are deterministic); Teleon-layer — never imports
src.baltor; never serves truth.
"""
from __future__ import annotations

from src.teleon.evolution.distiller import _MODEL_ROOT_COST, choose_strategy, distill

#: the efficiency/determinism strategies worth A/B-ing (the ones that trade accuracy for cost/determinism).
_AB_STRATEGIES = ("direct_api_rule", "deterministic_extract", "partial_rule_plus_model_residual", "model_downgrade")
KEEP_MODEL = "keep_model"  # the baseline: no descent, the full frontier model
_DEFAULT_MAX_ACCURACY_DROP = 0.03  # a descent may not drop accuracy more than this below the full-model baseline


def ceiling_scorer(capability: dict, strategy: str) -> float:
    """A deterministic representative scorer: a deterministic strategy is as accurate as the capability's
    deterministic coverage allows; the model baseline is high; a cheaper model is slightly below it. (Production
    swaps this for the capability's eval suite / a benchmark like rulearena_scorer.)"""
    if strategy == KEEP_MODEL:
        return 0.95
    if strategy == "model_downgrade":
        return 0.91
    # deterministic strategies: accurate exactly where the rule covers the cases
    return float(capability.get("deterministic_coverage_estimate", 0.0))


def rulearena_scorer(capability: dict, strategy: str) -> float:
    """A scorer wired to the RuleArena benchmark for RULE-GUIDED capabilities: deterministic forks compute the rule
    (benchmark deterministic accuracy); the model mis-applies rules (benchmark model accuracy). Ties the benchmark
    INTO the A/B decision."""
    from scripts.eval.rulearena_benchmark import benchmark
    b = benchmark()
    if strategy in ("direct_api_rule", "deterministic_extract", "partial_rule_plus_model_residual"):
        return b["deterministic_accuracy"]
    return b["model_accuracy"]  # keep_model / model_downgrade mis-apply rules like a bare LLM


def ab_test(capability: dict, *, scorer=ceiling_scorer, max_accuracy_drop: float = _DEFAULT_MAX_ACCURACY_DROP,
            policy=None) -> dict:
    """A/B the strategies for one capability: score each, keep the org-allowed ones within the accuracy tolerance
    of the full-model baseline, pick the CHEAPEST survivor (descend as far as possible without breaking accuracy)."""
    slot, cat = capability["capability_slot"], capability.get("category", "other")
    dc, cov = capability["determinism_ceiling"], capability.get("deterministic_coverage_estimate", 0.0)
    baseline_acc = float(scorer(capability, KEEP_MODEL))

    scored = [{"strategy": KEEP_MODEL, "accuracy": baseline_acc, "cost": _MODEL_ROOT_COST, "applied": True, "record": None}]
    for strat in _AB_STRATEGIES:
        d = distill(slot, category=cat, determinism_ceiling=dc, deterministic_coverage_estimate=cov,
                    strategy=strat, policy=policy)
        scored.append({"strategy": strat, "accuracy": float(scorer(capability, strat)),
                       "cost": d["record"]["per_call_cost_after"], "applied": d["applied"], "record": d["record"]})

    floor = baseline_acc - max_accuracy_drop
    eligible = [c for c in scored if c["applied"] and c["accuracy"] >= floor]
    winner = min(eligible, key=lambda c: (c["cost"], -c["accuracy"], c["strategy"])) if eligible else scored[0]
    prior = choose_strategy(dc)
    prior_row = next((c for c in scored if c["strategy"] == prior), None)
    prior_would_regress = bool(prior_row) and prior_row["accuracy"] < floor
    return {
        "capability_slot": slot, "category": cat, "determinism_ceiling": dc,
        "winner": winner["strategy"], "winner_accuracy": round(winner["accuracy"], 4),
        "winner_cost": winner["cost"], "baseline_accuracy": round(baseline_acc, 4),
        "accuracy_floor": round(floor, 4), "prior_strategy": prior,
        "prior_would_regress_accuracy": prior_would_regress, "winner_differs_from_prior": winner["strategy"] != prior,
        "scored": scored, "winning_record": winner["record"], "serves_truth": False,
    }


def ab_test_corpus(capabilities: list[dict], *, scorer=ceiling_scorer,
                   max_accuracy_drop: float = _DEFAULT_MAX_ACCURACY_DROP, policy=None) -> dict:
    """Run the A/B per capability, feed the winners to the meta-learner, and report the measured improvement:
    corrections (winner != prior), accuracy regressions PREVENTED (prior would have dropped below the floor), and
    cost saved vs the full-model baseline. The meta-learner now recommends the measured-best strategy per class."""
    from src.teleon.evolution.meta_learner import DistillationMetaLearner
    ml = DistillationMetaLearner()
    results, corrections, regressions_prevented, baseline_cost_total, winner_cost_total = [], 0, 0, 0.0, 0.0
    for cap in capabilities:
        r = ab_test(cap, scorer=scorer, max_accuracy_drop=max_accuracy_drop, policy=policy)
        results.append(r)
        if r["winning_record"] is not None:
            ml.record(r["winning_record"])
        corrections += int(r["winner_differs_from_prior"])
        # a regression is PREVENTED when the ceiling-only prior would have dropped below the accuracy floor but the
        # A/B winner stays within it (the harness caught a cheap-but-wrong fork the prior would have shipped).
        regressions_prevented += int(r["prior_would_regress_accuracy"] and r["winner_accuracy"] >= r["accuracy_floor"])
        baseline_cost_total += _MODEL_ROOT_COST
        winner_cost_total += r["winner_cost"]
    return {
        "n": len(capabilities), "corrections": corrections, "accuracy_regressions_prevented": regressions_prevented,
        "per_call_cost_saved_vs_model": round(baseline_cost_total - winner_cost_total, 6),
        "meta_learner": ml, "results": results,
        "all_winners_clear_accuracy_floor": all(r["winner_accuracy"] >= r["accuracy_floor"] for r in results),
        "serves_truth": False,
    }
