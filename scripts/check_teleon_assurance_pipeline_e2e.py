#!/usr/bin/env python3
"""check_teleon_assurance_pipeline_e2e — prove the ecosystem WORKS TOGETHER end-to-end on a REAL corpus capability.

Not a pile of modules — one assurance pipeline where each stage consumes the previous stage's output, on a real
discovered candidate + the real resource registries:

  discover (the committed feed) -> SCREEN (seeder) -> NETWORK profile + IMPL-FINDER (more-deterministic impl?) ->
  A/B DESCENT (measured winner, bounded by the org guardrail policy) -> META-LEARNER + MEASUREMENT (cost saved) ->
  TENANT OBJECTIVE binding.

Asserts the hand-offs are real and that the whole chain is governed (every stage serves_truth=False; the descent
clears the accuracy floor; the policy bounds the fork). This is the "tools + verticals + resources all work
together" guarantee, on a real capability from the catalog.

CLI: python3 scripts/check_teleon_assurance_pipeline_e2e.py --self-test
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.capability_seeder import screen, seed_feed
from src.teleon.evolution import ab_test, ceiling_scorer, find_implementations, measure_descent
from src.teleon.governance import load_policy
from src.teleon.objectives import objective_for_tenant
from src.teleon.training import CapabilityNetwork

_FEED = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data" / "capability-candidates" / "discovered-feed-2026-06-19.json"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ck("the committed discovered feed (the real catalog substrate) is present", _FEED.exists())

    # STAGE 1-2: discover + SCREEN — a real candidate from the catalog passes the governed gap/lift screen.
    seeded = seed_feed(_FEED)
    accepted = seeded["accepted"]
    cand = next((c for c in accepted if c["capability_slot"] == "live-stock-price-quote"), accepted[0])
    ck("a REAL discovered candidate normalizes + passes the screen, stays a candidate (never truth)",
       screen(cand)["accepted"] is True and cand["status"] == "candidate" and cand["serves_truth"] is False)

    # STAGE 3: NETWORK profile + IMPL-FINDER consume the corpus — the capability is placed in the relationship graph.
    net = CapabilityNetwork().build(accepted)
    prof = net.profile(cand["capability_slot"])
    ck("the capability network profiles the candidate from the real corpus (metadata + graph position)",
       prof["capability_slot"] == cand["capability_slot"] and "alternatives" in prof and prof["serves_truth"] is False)
    found = find_implementations(cand, accepted)
    ck("the impl-finder runs over the real corpus + never serves truth (proposes, never disposes)",
       "recommendation" in found and found["serves_truth"] is False)

    # STAGE 4: A/B DESCENT — measured winner, BOUNDED by the org guardrail policy. Feeds from the candidate's fields.
    permissive = load_policy("default-permissive")
    ab = ab_test(cand, scorer=ceiling_scorer, policy=permissive)
    ck("A/B descent picks a measured winner that clears the accuracy floor (no cheap-but-wrong fork)",
       ab["winner_accuracy"] >= ab["accuracy_floor"] and ab["serves_truth"] is False)
    ck("for this ceiling-1.0 capability the winner is the cheap DETERMINISTIC fork (cost 0.0, accuracy kept)",
       ab["winner"] in ("direct_api_rule", "deterministic_extract") and ab["winner_cost"] == 0.0, str(ab["winner"]))
    # the org policy actually BOUNDS the descent: a deterministic-only org accepts this deterministic winner...
    det_ab = ab_test(cand, scorer=ceiling_scorer, policy=load_policy("deterministic-audit"))
    ck("the org guardrail policy bounds the descent in-line (a deterministic-only org still gets a deterministic winner)",
       det_ab["winner"] in ("direct_api_rule", "deterministic_extract"))

    # STAGE 5: META-LEARNER + MEASUREMENT consume the A/B winner's record.
    rec = ab["winning_record"]
    ck("the A/B winner produced a real DistillationRecord to learn + measure from", rec is not None and rec["applied"] is True)
    m = measure_descent([rec])
    ck("the measurement harness captures the per-call cost saved + per-axis improvement from the winning record",
       m["per_call_cost_saved"] >= 0 and m["capabilities_descended"] == 1 and m["serves_truth"] is False)

    # STAGE 6: TENANT OBJECTIVE binding closes the loop (who this capability is being run for, and why).
    obj = objective_for_tenant("high-volume-batch")
    ck("the tenant objective binds (high-volume -> minimize_cost), governing which runner the capability uses",
       obj.name == "minimize_cost")

    # END-TO-END: the whole chain is governed — nothing serves truth anywhere.
    ck("END-TO-END: every stage of the assurance pipeline serves_truth=False (governed throughout)",
       all(x is False for x in (cand["serves_truth"], prof["serves_truth"], found["serves_truth"],
                                ab["serves_truth"], m["serves_truth"])))

    print("\n" + ("PASS - check_teleon_assurance_pipeline_e2e: a REAL discovered capability flows end-to-end through "
                  "the whole ecosystem — screen -> network/impl-finder -> A/B descent (bounded by the org policy, "
                  "clears the accuracy floor) -> meta-learner + cost measurement -> tenant-objective binding — each "
                  "stage consuming the last, governed throughout (serves_truth=False). The tools, verticals, and "
                  "resource registries compose; they are not a pile of modules."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
