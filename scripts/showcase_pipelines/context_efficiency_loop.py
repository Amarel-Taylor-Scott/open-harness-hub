#!/usr/bin/env python3
"""Showcase: the full context-efficiency (Friston) loop over a multi-turn session.

Ties together the context-efficiency thread end-to-end on a realistic working set:
  1. observe usage across turns        (usage_gated_compress.observe — the learned prior)
  2. classify the cohort + pick a curve (cohort_policy_selector — consumer behavior)
  3. apply the prediction-error gate     (usage_gated_compress.run with the cohort weights+budget)
  4. rehydrate on a prediction MISS      (a paged-out item is needed → observe re-promotes it)
  5. report the re-read tokens saved      (the Friston payoff — pay full cost only on surprise)

The scenario is a power-user on a large stable codebase: a few hot files cited every turn, a
churning config, and a frozen vendored blob re-read as ritual. The loop learns the shape,
compresses the predictable substrate to handles, keeps the proven working set, and when a
later turn references a paged-out file (a prediction miss) the prior re-promotes it — exactly
the brain's "spend expensive bits only where prediction fails."

Run:  python3 scripts/showcase_pipelines/context_efficiency_loop.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.compression.cohort_policy_selector import compress_with_cohort_policy
from scripts.processors.compression.usage_gated_compress import empty_prior, observe, run as gate_run

#: A synthetic large-codebase working set: 2 HOT files cited every turn, a large STABLE
#: substrate (8 files re-read every turn but never cited — the power-user signature), a
#: churning config, and the pinned system prompt.
_WORKING_SET = (
    [{"id": f"hot-{i}.py", "text": "def core(): " + "logic ; " * 40} for i in range(2)]
    + [{"id": f"substrate-{i}.py", "text": "stable module body " * 40} for i in range(8)]
    + [{"id": "config.yaml", "text": "settings: " + "k: v ; " * 40}]
    + [{"id": "system", "text": "You are the assistant.", "pinned": True}]
)
_HOT_IDS = [f"hot-{i}.py" for i in range(2)]
_WARMUP_TURNS = 10


def run(*, working_set: list[dict[str, Any]] = _WORKING_SET,
        warmup_turns: int = _WARMUP_TURNS) -> dict[str, Any]:
    """Run the multi-turn loop; return the cohort, the plan, and the re-read savings."""
    served = [it["id"] for it in working_set if not it.get("pinned")]
    prior = empty_prior()
    # 1-2. learn the usage prior over the warmup turns (hot files cited; config churns).
    for turn in range(1, warmup_turns + 1):
        prior = observe(prior, served_ids=served, cited_ids=list(_HOT_IDS),
                        changed_ids=["config.yaml"] if turn % 2 == 0 else [], now_turn=turn)
    # 2-3. the WIRED entry point: classify the cohort, derive the budget, apply the gate
    # with the cohort's weights — one call (cohort_policy_selector.compress_with_cohort_policy).
    wired = compress_with_cohort_policy(items=working_set, prior=prior, now_turn=warmup_turns + 1)
    policy, budget, plan = wired["policy"], wired["token_budget"], wired["plan"]
    # 4. a prediction MISS: a paged-out item is referenced next turn → re-promote it.
    rehydrated = None
    if plan["paged_out"]:
        missed = plan["paged_out"][0]["id"]
        learned = observe(prior, served_ids=[i for i in served if i != missed],
                          cited_ids=[missed], now_turn=warmup_turns + 1)  # cited though not served = miss
        re_plan = gate_run(items=working_set, prior=learned, token_budget=budget,
                           now_turn=warmup_turns + 2, weights=policy["weights"])["plan"]
        before = {p["id"]: p["priority"] for p in plan["items"]}[missed]
        after = {p["id"]: p["priority"] for p in re_plan["items"]}[missed]
        rehydrated = {"item": missed, "priority_before": before, "priority_after": after,
                      "re_promoted": after > before}
    return {"cohort": policy["cohort"], "policy_weights": policy["weights"],
            "budget_fraction": policy["budget_fraction"], "budget_tokens": budget,
            "tiers": {k: len(v) for k, v in plan["tiers"].items()},
            "paged_out": [p["id"] for p in plan["paged_out"]],
            "tokens_kept": plan["tokens_kept"], "naive_reread_tokens": plan["naive_reread_tokens"],
            "predicted_savings_fraction": plan["predicted_savings_fraction"],
            "rehydrated_on_miss": rehydrated, "serves_truth": False}


def _self_test() -> int:
    out = run()
    # A power-user-on-stable-substrate shape is recognized.
    assert out["cohort"] == "power_user_large_substrate", out["cohort"]
    # The pin is kept; frozen never-cited substrate pages out to handles.
    assert any(i.startswith("substrate-") for i in out["paged_out"])
    assert "system" not in out["paged_out"]
    # Real re-read savings (we serve far fewer tokens than a naive keep-everything prefill).
    assert out["tokens_kept"] < out["naive_reread_tokens"]
    assert 0 < out["predicted_savings_fraction"] < 1
    # The prediction MISS re-promotes the paged-out item (the learning loop closes).
    assert out["rehydrated_on_miss"] is not None and out["rehydrated_on_miss"]["re_promoted"] is True
    # Derived-plan honesty.
    assert out["serves_truth"] is False
    # Deterministic.
    assert json.dumps(run(), sort_keys=True) == json.dumps(run(), sort_keys=True)
    print(f"PASS — context_efficiency_loop: learned the '{out['cohort']}' cohort over "
          f"{_WARMUP_TURNS} turns, applied the cohort curve (budget {out['budget_fraction']}), "
          f"paged the frozen substrate to handles, saved {out['predicted_savings_fraction']:.0%} of "
          "the naive re-read, and re-promoted the paged-out item on a prediction miss; deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Context-efficiency (Friston) loop showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(json.dumps(run(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
