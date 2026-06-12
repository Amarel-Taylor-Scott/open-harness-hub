#!/usr/bin/env python3
"""scripts.processors.compression.cohort_policy_selector — pick the compression curve from usage SHAPE.

The prediction-error-gated thesis (`docs/concepts/prediction-error-gated-context.md`, Axis 3):
the cache/re-read ratio is NOT one curve — it is cohort-dependent. A power-user on a large
stable codebase re-reads ~everything (compress the substrate hard, keep the working set full);
a one-off/fresh-context user generates mostly-new context (barely compress — everything is
surprise, and compressing what the model hasn't absorbed would HURT); an iterating-on-a-
deliverable user churns a growing artifact (gate on volatility — re-read what changed, page out
what froze). `usage_gated_compress` has the per-ITEM prior; this selector adds the missing
per-COHORT shape → it reads a usage prior, classifies the tenant's shape, and emits the
compression POLICY (budget fraction + the gate's utility/volatility/recency weights) that
`usage_gated_compress.run(...)` should be parameterized with.

Governance: a tenant we have too little data on → the UNKNOWN cohort → the CONSERVATIVE policy
(keep most, compress little). Never over-compress context for a usage shape we don't yet
understand — the same "novelty = keep" principle as the per-item cold start. Deterministic:
same usage shape → byte-identical policy.

Public API:
    from scripts.processors.compression.cohort_policy_selector import summarize_usage, select_policy, run
    shape = summarize_usage(prior)            # prior = a usage_gated_compress prior
    policy = select_policy(shape)             # -> {cohort, budget_fraction, weights, ...}
    out = run(prior=prior)                    # shape + policy in one envelope

CLI / self-test:
    python3 scripts/processors/compression/cohort_policy_selector.py
    python3 -m scripts.processors.compression.cohort_policy_selector
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

# ── Configuration constants (single source of truth; No-Magic-Values) ─────────

#: Minimum total observations (served events) before we trust a cohort call. Below
#: this we stay conservative — too little signal to compress aggressively.
MIN_OBSERVATIONS = 12

#: Cohort thresholds on the usage-shape ratios (all in [0,1]).
#: fresh_ratio = items seen <=1 time / distinct items (lots of brand-new context).
FRESH_RATIO_THRESHOLD = 0.6
#: churn_ratio = mean(changed/served) (the source keeps changing → must re-read).
CHURN_RATIO_THRESHOLD = 0.3
#: reread_ratio = mean((served-cited)/served) (served a lot, cited rarely = ritual re-read).
REREAD_RATIO_THRESHOLD = 0.6

#: Cohort names (single definition; the policy + tests read these).
COHORT_FRESH = "fresh_oneoff"
COHORT_ITERATING = "iterating_deliverable"
COHORT_POWER = "power_user_large_substrate"
COHORT_BALANCED = "balanced"
COHORT_UNKNOWN = "unknown_insufficient_data"

#: The compression policy per cohort. `budget_fraction` = how much of the naive full
#: re-read to KEEP (high = barely compress); the weights parameterize the
#: `usage_gated_compress` gate (utility + volatility + recency, summing to 1.0).
#: These are the "compression curves" the thesis calls for.
COHORT_POLICY: dict[str, dict[str, Any]] = {
    # Fresh/one-off: everything is surprise → keep almost all; recency matters most.
    COHORT_FRESH: {"budget_fraction": 0.9, "aggressiveness": "minimal",
                   "weights": {"utility": 0.4, "volatility": 0.15, "recency": 0.45},
                   "rationale": "mostly-new context is genuine surprise — compressing it would hurt"},
    # Iterating: a churning artifact → moderate keep; VOLATILITY dominates (re-read what changed).
    COHORT_ITERATING: {"budget_fraction": 0.6, "aggressiveness": "moderate",
                       "weights": {"utility": 0.45, "volatility": 0.45, "recency": 0.1},
                       "rationale": "a changing artifact must be re-read where it changed; frozen parts page out"},
    # Power user on a large stable substrate → compress HARD; UTILITY dominates (keep proven).
    COHORT_POWER: {"budget_fraction": 0.35, "aggressiveness": "aggressive",
                   "weights": {"utility": 0.7, "volatility": 0.2, "recency": 0.1},
                   "rationale": "a large stable substrate the model has absorbed — keep the proven working set, page the rest"},
    # Balanced → the usage_gated_compress defaults.
    COHORT_BALANCED: {"budget_fraction": 0.55, "aggressiveness": "balanced",
                      "weights": {"utility": 0.55, "volatility": 0.3, "recency": 0.15},
                      "rationale": "mixed usage — the default prediction-error gate"},
    # Unknown → CONSERVATIVE: keep most; never over-compress a shape we don't understand.
    COHORT_UNKNOWN: {"budget_fraction": 0.85, "aggressiveness": "conservative",
                     "weights": {"utility": 0.5, "volatility": 0.2, "recency": 0.3},
                     "rationale": "too little usage history — stay conservative until the shape is known"},
}

RATIO_DECIMALS = 6


def summarize_usage(prior: dict[str, Any]) -> dict[str, Any]:
    """Derive the cohort SHAPE signals from a `usage_gated_compress` prior."""
    items = (prior or {}).get("items", {})
    distinct = len(items)
    total_served = sum(int(s.get("served", 0)) for s in items.values())
    if distinct == 0 or total_served == 0:
        return {"distinct_items": distinct, "total_served": total_served,
                "fresh_ratio": 0.0, "churn_ratio": 0.0, "reread_ratio": 0.0}
    fresh = sum(1 for s in items.values() if int(s.get("served", 0)) <= 1)
    churn = sum((int(s.get("changed", 0)) / int(s["served"])) for s in items.values() if int(s.get("served", 0)))
    reread = sum(((int(s["served"]) - int(s.get("cited", 0))) / int(s["served"]))
                 for s in items.values() if int(s.get("served", 0)))
    n_served_items = sum(1 for s in items.values() if int(s.get("served", 0)))
    return {"distinct_items": distinct, "total_served": total_served,
            "fresh_ratio": round(fresh / distinct, RATIO_DECIMALS),
            "churn_ratio": round(churn / n_served_items, RATIO_DECIMALS),
            "reread_ratio": round(reread / n_served_items, RATIO_DECIMALS)}


def classify(shape: dict[str, Any]) -> str:
    """Map a usage shape to a cohort (order matters: data-sufficiency → fresh → churn → reread)."""
    if shape["total_served"] < MIN_OBSERVATIONS:
        return COHORT_UNKNOWN
    if shape["fresh_ratio"] >= FRESH_RATIO_THRESHOLD:
        return COHORT_FRESH
    if shape["churn_ratio"] >= CHURN_RATIO_THRESHOLD:
        return COHORT_ITERATING
    if shape["reread_ratio"] >= REREAD_RATIO_THRESHOLD:
        return COHORT_POWER
    return COHORT_BALANCED


def select_policy(shape: dict[str, Any]) -> dict[str, Any]:
    """Classify the shape and return the compression policy (cohort + budget + gate weights)."""
    cohort = classify(shape)
    policy = dict(COHORT_POLICY[cohort])
    return {"cohort": cohort, **policy, "shape": shape}


def run(*, prior: dict[str, Any]) -> dict[str, Any]:
    """One-call: usage prior → shape → policy. The policy parameterizes usage_gated_compress."""
    if not isinstance(prior, dict):
        raise TypeError(f"prior must be a usage_gated_compress prior dict, got {type(prior).__name__}")
    shape = summarize_usage(prior)
    return {"policy": select_policy(shape)}


def _self_test() -> int:
    from scripts.processors.compression.usage_gated_compress import empty_prior, observe, run as gate_run

    # POWER USER: many items served every turn, only a few ever cited (ritual re-read),
    # nothing churns — the large stable substrate.
    power = empty_prior()
    served = [f"f{i}" for i in range(10)]
    for turn in range(1, 9):
        power = observe(power, served_ids=served, cited_ids=["f0", "f1"], now_turn=turn)
    p_shape = summarize_usage(power)
    assert classify(p_shape) == COHORT_POWER, p_shape
    p_policy = select_policy(p_shape)
    assert p_policy["aggressiveness"] == "aggressive" and p_policy["budget_fraction"] < 0.5
    assert p_policy["weights"]["utility"] >= 0.6  # keep the proven, page the rest

    # ITERATING: a small set, churning hard (changed most turns), reasonably cited.
    iterating = empty_prior()
    for turn in range(1, 9):
        iterating = observe(iterating, served_ids=["a", "b", "c"], cited_ids=["a", "b"],
                            changed_ids=["a", "b", "c"], now_turn=turn)
    i_shape = summarize_usage(iterating)
    assert classify(i_shape) == COHORT_ITERATING, i_shape
    assert select_policy(i_shape)["weights"]["volatility"] >= 0.4  # re-read what changed

    # FRESH/one-off: each turn brings brand-new items, rarely seen twice.
    fresh = empty_prior()
    for turn in range(1, 9):
        fresh = observe(fresh, served_ids=[f"new-{turn}-{j}" for j in range(3)],
                        cited_ids=[f"new-{turn}-0"], now_turn=turn)
    f_shape = summarize_usage(fresh)
    assert classify(f_shape) == COHORT_FRESH, f_shape
    f_policy = select_policy(f_shape)
    assert f_policy["aggressiveness"] == "minimal" and f_policy["budget_fraction"] >= 0.85

    # UNKNOWN: too little data → conservative (never over-compress what we don't understand).
    sparse = observe(empty_prior(), served_ids=["x"], cited_ids=["x"], now_turn=1)
    u_shape = summarize_usage(sparse)
    assert classify(u_shape) == COHORT_UNKNOWN
    assert select_policy(u_shape)["aggressiveness"] == "conservative"

    # The policy is ACTIONABLE: its budget_fraction + weights feed usage_gated_compress.
    # A power-user policy compresses HARDER (keeps fewer tokens) than a fresh policy on the
    # same items — the curves actually differ.
    items = [{"id": fid, "text": "stable code body " * 30} for fid in served]
    naive = sum(len("stable code body " * 30).__class__ and 1 for _ in items)  # placeholder
    full_tokens = sum(len(("stable code body " * 30).split()) for _ in items)
    power_budget = max(1, int(full_tokens * p_policy["budget_fraction"]))
    fresh_budget = max(1, int(full_tokens * f_policy["budget_fraction"]))
    assert power_budget < fresh_budget  # power-user keeps less of the same substrate
    power_plan = gate_run(items=items, prior=power, token_budget=power_budget, now_turn=9)["plan"]
    fresh_plan = gate_run(items=items, prior=power, token_budget=fresh_budget, now_turn=9)["plan"]
    assert power_plan["tokens_kept"] <= fresh_plan["tokens_kept"]  # the curve bites

    # Deterministic; on_error=raise.
    assert json.dumps(run(prior=power), sort_keys=True) == json.dumps(run(prior=power), sort_keys=True)
    raised = False
    try:
        run(prior="not a prior")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised

    # Empty prior → unknown/conservative, never a crash.
    assert select_policy(summarize_usage(empty_prior()))["cohort"] == COHORT_UNKNOWN

    print(
        "PASS — cohort_policy_selector: usage SHAPE → cohort (power/iterating/fresh/balanced/"
        "unknown) → the compression curve (budget_fraction + utility/volatility/recency weights); "
        "power-user compresses the stable substrate hard, fresh barely compresses, unknown stays "
        "conservative; policy feeds usage_gated_compress; deterministic"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Pick the compression curve from usage shape.")
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
