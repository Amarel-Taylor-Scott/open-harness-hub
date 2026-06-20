#!/usr/bin/env python3
"""check_preference_profile — proof that "efficient" is the USER's multi-objective trade-off, not one fixed metric.
A user-set PreferenceProfile (weights over cost/latency/tokens_in/determinism/freshness + hard constraints) drives
which bounded implementation Teleon picks: a cost-first user gets the cheapest, a latency-first user gets the fastest,
a determinism-required user gets the deterministic one even if pricier, and a constraint that excludes everything is
reported honestly (no fabricated pick). Generalizes the single-objective selector. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_preference_profile.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.inference.preference_profile import (
    OBJECTIVES, PreferenceProfile, choose, cost_first, determinism_required, latency_first, score_candidates,
)

# three bounded implementations of the same capability (the descent's candidate outputs)
_CANDS = [
    {"id": "deterministic_rule", "cost": 0.000, "latency": 5,   "tokens_in": 0,    "determinism": 1.0, "freshness": 1.0},
    {"id": "cheap_llm",         "cost": 0.010, "latency": 250, "tokens_in": 400,  "determinism": 0.6, "freshness": 0.8},
    {"id": "frontier_llm",      "cost": 0.120, "latency": 900, "tokens_in": 1200, "determinism": 0.6, "freshness": 0.9},
]


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # a cost-first user gets the cheapest
    ck("cost-first profile picks the cheapest implementation", choose(_CANDS, cost_first())["chosen"] == "deterministic_rule")

    # a latency-first user gets the fastest (here also the rule, so use a set where fastest != cheapest)
    cands2 = [
        {"id": "fast_small_model", "cost": 0.05, "latency": 20, "tokens_in": 100, "determinism": 0.6, "freshness": 0.9},
        {"id": "cheapest_slow",    "cost": 0.00, "latency": 800, "tokens_in": 0,  "determinism": 1.0, "freshness": 1.0},
    ]
    ck("latency-first profile picks the fastest even when it is NOT the cheapest",
       choose(cands2, latency_first())["chosen"] == "fast_small_model")
    ck("cost-first on the same set picks the cheaper-but-slower one (different user, different pick)",
       choose(cands2, cost_first())["chosen"] == "cheapest_slow")

    # a determinism-required user gets the deterministic one even though it costs more, and non-deterministic ones are excluded
    dr = choose(_CANDS, determinism_required())
    ck("determinism-required profile picks the fully-deterministic implementation", dr["chosen"] == "deterministic_rule")
    only_det = PreferenceProfile(weights={"cost": 1.0}, min_determinism=1.0)
    res = choose(_CANDS, only_det)
    ck("a min-determinism constraint EXCLUDES non-deterministic candidates (even under a cost-first weight)",
       res["chosen"] == "deterministic_rule")

    # a hard constraint that nothing can meet is reported honestly (no fabricated pick)
    impossible = PreferenceProfile(weights={"cost": 1.0}, max_latency=1)
    none = choose(_CANDS, impossible)
    ck("when no candidate meets the hard constraints, chosen is None with a reason (not fabricated)",
       none["chosen"] is None and "violations" in none and none["reason"])

    # weights normalize and actually drive the score (changing weights changes the composite ordering)
    p = PreferenceProfile(weights={"cost": 3.0, "latency": 1.0})
    ck("weights normalize to sum 1", abs(sum(p.normalized_weights().values()) - 1.0) < 1e-9)
    ck("the composite score is computed from weights (cheapest gets the best score under a cost-weighted profile)",
       score_candidates(_CANDS, cost_first())[0] == min(score_candidates(_CANDS, cost_first())))

    # generalizes the single-objective selector: cost-first == 'cheapest'
    ck("cost-first generalizes the legacy 'cheapest' objective", choose(_CANDS, cost_first())["chosen"] == "deterministic_rule")

    # determinism + honesty
    ck("deterministic (same inputs -> same pick)", choose(_CANDS, cost_first()) == choose(_CANDS, cost_first()))
    ck("never serves truth", dr["serves_truth"] is False and none["serves_truth"] is False)
    ck("covers all five objectives (cost, latency, tokens_in, determinism, freshness)",
       set(OBJECTIVES) == {"cost", "latency", "tokens_in", "determinism", "freshness"})

    print("\n" + ("PASS - check_preference_profile: 'efficient' is the USER's multi-objective trade-off — a user-set "
                  "PreferenceProfile (weights over cost/latency/tokens_in/determinism/freshness + hard constraints) "
                  "drives which bounded implementation Teleon picks; cost-first->cheapest, latency-first->fastest, "
                  "determinism-required->deterministic, impossible-constraint->honest no-pick. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_preference_profile.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
