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

from src.teleon.evolution.distiller import _MODEL_ROOT_COST, DistillationRecord, choose_strategy, distill
from src.teleon.evolution.token_reduction import compress_skill, estimate_tokens

#: the efficiency/determinism strategies worth A/B-ing (the ones that trade accuracy for cost/determinism).
_AB_STRATEGIES = ("direct_api_rule", "deterministic_extract", "partial_rule_plus_model_residual", "model_downgrade")
_DETERMINISTIC = ("direct_api_rule", "deterministic_extract", "partial_rule_plus_model_residual")
KEEP_MODEL = "keep_model"  # the baseline: no descent, the full frontier model
_DEFAULT_MAX_ACCURACY_DROP = 0.03  # a descent may not drop accuracy more than this below the full-model baseline
_DEFAULT_PROMPT_TOKENS_IN = 800    # representative input tokens for a model strategy when no skill prompt is given
_DEFAULT_TOKENS_OUT = 200          # representative output tokens for a model strategy


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
            policy=None, skill_text: str | None = None) -> dict:
    """A/B the strategies for one capability: score each (accuracy + cost + TOKENS in/out), keep the org-allowed
    ones within the accuracy tolerance of the full-model baseline, pick the cheapest-then-fewest-tokens survivor
    (descend as far as possible without breaking accuracy). When ``skill_text`` is given, a prompt_compression
    candidate is A/B-tested too — same model, fewer INPUT tokens (token-proportional cost), applied only if the
    compression stays lossless."""
    slot, cat = capability["capability_slot"], capability.get("category", "other")
    dc, cov = capability["determinism_ceiling"], capability.get("deterministic_coverage_estimate", 0.0)
    skill_text = skill_text or capability.get("skill_text")  # a capability may carry its own skill prompt
    baseline_acc = float(scorer(capability, KEEP_MODEL))
    base_tin = estimate_tokens(skill_text) if skill_text else _DEFAULT_PROMPT_TOKENS_IN

    scored = [{"strategy": KEEP_MODEL, "accuracy": baseline_acc, "cost": _MODEL_ROOT_COST, "applied": True,
               "record": None, "tokens_in": base_tin, "tokens_out": _DEFAULT_TOKENS_OUT}]
    for strat in _AB_STRATEGIES:
        d = distill(slot, category=cat, determinism_ceiling=dc, deterministic_coverage_estimate=cov,
                    strategy=strat, policy=policy)
        is_det = strat in _DETERMINISTIC
        scored.append({"strategy": strat, "accuracy": float(scorer(capability, strat)),
                       "cost": d["record"]["per_call_cost_after"], "applied": d["applied"], "record": d["record"],
                       "tokens_in": 0 if is_det else base_tin, "tokens_out": 0 if is_det else _DEFAULT_TOKENS_OUT})

    compression = None
    if skill_text:
        compression = compress_skill(slot, skill_text, must_keep=tuple(capability.get("must_keep", ())))
        ratio = compression["tokens_in_after"] / max(1, compression["tokens_in_before"])  # token-billed cost scales w/ input
        comp_cost = round(_MODEL_ROOT_COST * ratio, 6)
        comp_acc = baseline_acc if compression["lossless"] else baseline_acc - 0.5  # a lossy compression regresses
        comp_rec = DistillationRecord(
            capability_slot=slot, category=cat, strategy="prompt_compression", determinism_ceiling=dc,
            per_call_cost_before=_MODEL_ROOT_COST, per_call_cost_after=comp_cost, distill_cost=0.05, coverage=1.0,
            residual_fraction=0.0, equivalence_verified=compression["lossless"], lossless=compression["lossless"],
            policy_allowed=True, applied=compression["lossless"], fork_runner_id=f"{slot}::token_reduced",
            improvement_axes=("tokens_in", "cost")).as_dict()
        scored.append({"strategy": "prompt_compression", "accuracy": comp_acc, "cost": comp_cost,
                       "applied": compression["lossless"], "record": comp_rec,
                       "tokens_in": compression["tokens_in_after"], "tokens_out": _DEFAULT_TOKENS_OUT})

    floor = baseline_acc - max_accuracy_drop
    eligible = [c for c in scored if c["applied"] and c["accuracy"] >= floor]
    # descend as far as possible: cheapest cost, then fewest TOTAL tokens, then highest accuracy, then name.
    winner = (min(eligible, key=lambda c: (c["cost"], c["tokens_in"] + c["tokens_out"], -c["accuracy"], c["strategy"]))
              if eligible else scored[0])
    prior = choose_strategy(dc)
    prior_row = next((c for c in scored if c["strategy"] == prior), None)
    prior_would_regress = bool(prior_row) and prior_row["accuracy"] < floor
    return {
        "capability_slot": slot, "category": cat, "determinism_ceiling": dc,
        "winner": winner["strategy"], "winner_accuracy": round(winner["accuracy"], 4),
        "winner_cost": winner["cost"], "winner_tokens_in": winner["tokens_in"], "winner_tokens_out": winner["tokens_out"],
        "baseline_accuracy": round(baseline_acc, 4), "baseline_tokens_in": base_tin,
        "tokens_saved_by_compression": (compression["tokens_saved"] if compression else 0),
        "compression_lossless": (compression["lossless"] if compression else None),
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
    results, corrections, regressions_prevented = [], 0, 0
    baseline_cost_total = winner_cost_total = baseline_tokens_total = winner_tokens_total = 0.0
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
        baseline_tokens_total += r["baseline_tokens_in"] + _DEFAULT_TOKENS_OUT
        winner_tokens_total += r["winner_tokens_in"] + r["winner_tokens_out"]
    return {
        "n": len(capabilities), "corrections": corrections, "accuracy_regressions_prevented": regressions_prevented,
        "per_call_cost_saved_vs_model": round(baseline_cost_total - winner_cost_total, 6),
        "per_call_tokens_saved_vs_model": round(baseline_tokens_total - winner_tokens_total, 3),
        "meta_learner": ml, "results": results,
        "all_winners_clear_accuracy_floor": all(r["winner_accuracy"] >= r["accuracy_floor"] for r in results),
        "serves_truth": False,
    }
