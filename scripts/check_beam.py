#!/usr/bin/env python3
"""check_beam — System 5 (multi-candidate composition): verify-filter + simulate-rank + keep the best, no execution.

Proves: beam_compose keeps only VERIFIED candidates (a cycle is dropped), ranks the survivors by SIMULATED cost (cheapest
chosen), respects beam_width, and is honest (chosen=None) when nothing verifies. serves_truth=false.

  python3 scripts/check_beam.py --self-test
"""
from __future__ import annotations

import uuid

from src.teleon.economics import observation_store as OBS
from src.teleon.synthesis import beam
from src.teleon.inference.preference_profile import cost_first


_SHARD = uuid.uuid4().hex[:12]   # isolate this check's economic store from concurrent subprocesses


def _seed(cost):
    rid = f"test.beam.{uuid.uuid4().hex[:10]}"
    OBS.record_observation(rid, source="test", cost=cost, latency_ms=10, shard=_SHARD)
    return rid


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    cheap, pricey = _seed(0.001), _seed(0.050)
    # two VERIFIED single-node candidates (plane=embedding consumes text=graph-input) with different component economics
    cand_cheap = {"nodes": [{"step": "n", "component": cheap, "plane": "embedding"}], "edges": []}
    cand_pricey = {"nodes": [{"step": "n", "component": pricey, "plane": "embedding"}], "edges": []}
    # an UNVERIFIABLE candidate: a 2-cycle
    cand_broken = {"nodes": [{"step": "a", "plane": "llm"}, {"step": "b", "plane": "llm"}], "edges": [["a", "b"], ["b", "a"]]}

    res = beam.beam_compose([cand_pricey, cand_cheap, cand_broken], profile=cost_first(), beam_width=2, shard=_SHARD)
    ck("the cheaper VERIFIED candidate is chosen (simulated ranking, no execution)", res["chosen"] is cand_cheap)
    ck("the unverifiable candidate (cycle) is dropped, not ranked", res["n_verified"] == 2 and res["n_candidates"] == 3)
    ck("beam_width caps the kept set", len(res["beam"]) == 2)
    ck("each beam entry carries the verdict + simulated estimate + score", all({"candidate", "verdict", "estimate", "score"} <= set(b) for b in res["beam"]))

    empty = beam.beam_compose([cand_broken], profile=cost_first(), shard=_SHARD)
    ck("honest empty when nothing verifies (chosen=None)", empty["chosen"] is None and empty["n_verified"] == 0)
    ck("serves_truth=false", res["serves_truth"] is False)

    print("\n" + ("PASS - check_beam: verify-filter + simulate-rank keeps the best of many candidate DAGs without "
                  "executing them; cycles dropped; honest when none verify." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
