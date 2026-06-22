#!/usr/bin/env python3
"""check_agentic_loop_catalog — the agentic-loop seeds are well-formed and every loop descends (bounded < unbounded).

Each loop is perceive→reason→act→verify→iterate; the catalog declares an UNBOUNDED (frontier-every-step) cost model and
a BOUNDED (cheapest-plane + early-stop + LLM-as-supervisor) cost model. This proves: every loop has steps + both modes
+ declared tool_planes (in tool_planes.json) + a real maps_to domain (in capability_taxonomy); and the bounded cost is
strictly lower (the descent actually saves). serves_truth=false.

  python3 scripts/check_agentic_loop_catalog.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAT = REPO / "architecture" / "agentic_loop_catalog.json"


def costs(loop: dict) -> tuple[float, float]:
    """(unbounded, bounded) cost for a loop, computed from its declared model (no magic in the viz/check)."""
    steps = max(1, len(loop.get("loop", [])))
    ub, bd = loop["unbounded"], loop["bounded"]
    unbounded = steps * ub["iterations"] * ub["step_cost"]
    bounded = steps * bd["iterations"] * bd["step_cost"] + bd.get("supervise", 0.0)
    return round(unbounded, 2), round(bounded, 2)


def _self_test() -> int:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    loops = cat["loops"]
    plane_ids = {p["plane"] for p in json.loads((REPO / "architecture" / "tool_planes.json").read_text(encoding="utf-8"))["planes"]}
    domains = {d["domain"] for d in json.loads((REPO / "architecture" / "capability_taxonomy.json").read_text(encoding="utf-8"))["domains"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"catalog of agentic LOOPS ({len(loops)}) + emerging frontiers ({len(cat.get('frontiers', []))})",
       len(loops) >= 12 and len(cat.get("frontiers", [])) >= 5)
    ck("every loop has >=3 steps + an unbounded + a bounded mode",
       all(len(L.get("loop", [])) >= 3 and L.get("unbounded") and L.get("bounded") for L in loops))
    bad_plane = sorted({pl for L in loops for pl in L.get("tool_planes", []) if pl not in plane_ids})
    ck("every loop's tool_planes are declared in tool_planes.json", not bad_plane, str(bad_plane))
    bad_map = sorted({L["maps_to"] for L in loops if L.get("maps_to") not in domains and L.get("maps_to") != "software_engineering"})
    ck("every loop maps to a real capability domain (or the new software_engineering)", not bad_map, str(bad_map))
    not_descending = [L["id"] for L in loops if not (costs(L)[1] < costs(L)[0])]
    ck("EVERY loop descends — bounded cost strictly < unbounded cost", not not_descending, str(not_descending))
    pcts = [round(100 * (u - b) / u, 1) for L in loops for (u, b) in [costs(L)]]
    avg = round(sum(pcts) / len(pcts), 1)
    ck(f"the descent is material (avg {avg}% cheaper bounded vs unbounded across loops)", avg >= 70)
    ck("each loop reserves the LLM for supervision / uses early-stop (the bounded discipline)",
       all(L["bounded"].get("early_stop") for L in loops))
    ck("serves_truth=false", cat.get("serves_truth") is False)

    print("\n" + (f"PASS - check_agentic_loop_catalog: {len(loops)} agentic loops, each perceive→act→verify→iterate; every "
                  f"one descends unbounded→bounded (avg {avg}% cheaper) using declared tool planes; +{len(cat.get('frontiers', []))} "
                  "emerging frontiers. serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
