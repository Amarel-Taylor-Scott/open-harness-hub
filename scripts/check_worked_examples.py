#!/usr/bin/env python3
"""check_worked_examples — concrete end-to-end capability examples that stay TIED to the real system.

Proves, for each worked example: (1) the REAL planner classifies the request to the stated capability_type
(classify_capability_type is re-run here — an example can't drift from the router, and this is exactly the assertion that
would have caught 'find contact info' mis-routing to hub_population); (2) it maps to a real agentic loop + waste
archetype; (3) every bounded step names a declared tool-plane + registry tools that exist in tool_registry; (4) the
heuristics are real; (5) the bounded path is cheaper than the unbounded one (the descent holds); (6) truth-bearing
examples carry Baltor governance (provenance + honest-MISSING). Prints each example's descent. serves_truth posture is
per-example (the descent is Teleon; truth-bearing OUTPUTS are Baltor).

  python3 scripts/check_worked_examples.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.capability_planner import classify_capability_type

REPO = Path(__file__).resolve().parents[1]


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    ex = _load("worked_examples.json")["examples"]
    loops = {L["id"] for L in _load("agentic_loop_catalog.json")["loops"]}
    archetypes = {a["id"] for a in _load("inefficient_pipeline_archetypes.json")["archetypes"]}
    heuristics = {h["id"] for h in _load("optimization_heuristics.json")["heuristics"]}
    tool_ids = {t["id"] for t in _load("tool_registry.json")["tools"]}
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"worked examples present ({len(ex)})", len(ex) >= 2)
    rows = []
    for e in ex:
        eid = e["id"]
        # (1) THE anti-drift tie: the real planner must agree with the stated type
        got = classify_capability_type(e["request"])
        ck(f"[{eid}] planner routes request -> {e['capability_type']}", got == e["capability_type"],
           f"planner said {got!r}")
        # (2) loop + archetype real
        ck(f"[{eid}] loop is real", e["loop"] in loops, e["loop"])
        ck(f"[{eid}] archetype is real", e["archetype"] in archetypes, e["archetype"])
        # (3) bounded steps reference real planes + real registry tools
        steps = e["bounded"]["steps"]
        bad_plane = sorted({s["plane"] for s in steps if s["plane"] not in planes})
        ck(f"[{eid}] every step's plane is declared", not bad_plane, str(bad_plane))
        bad_tool = sorted({t for s in steps for t in s.get("registry_tools", []) if t not in tool_ids})
        ck(f"[{eid}] every registry tool exists in tool_registry", not bad_tool, str(bad_tool))
        # (4) heuristics real
        bad_h = [h for h in e.get("heuristics", []) if h not in heuristics]
        ck(f"[{eid}] heuristics are real", not bad_h, str(bad_h))
        # (5) the descent holds
        u, b = e["unbounded"]["est_cost_usd"], e["bounded"]["est_cost_usd"]
        ck(f"[{eid}] bounded cheaper than unbounded", b < u, f"{b} !< {u}")
        # (6) truth-bearing -> Baltor governance
        g = e.get("governance", {})
        if g.get("serves_truth"):
            ck(f"[{eid}] truth-bearing example carries provenance + honest-MISSING",
               bool(g.get("provenance")) and bool(g.get("honest_missing")))
        # at least one deterministic step before any LLM; LLM (if any) is residual/supervisor, never the whole task
        llm_roles = {s["llm_role"] for s in steps}
        ck(f"[{eid}] LLM is residual/supervisor only (or none), never the whole task",
           llm_roles <= {"none", "residual", "supervisor"} and any(s["deterministic"] for s in steps))
        pct = round((u - b) / u * 100)
        rows.append((eid, e["capability_type"], e["loop"], pct, g.get("truth_owner", "-")))

    print("\n  descent summary (representative costs):")
    for eid, ct, loop, pct, owner in rows:
        print(f"    {eid:26s} {ct:26s} loop={loop:11s} ~{pct:>3d}% cheaper  truth->{owner}")
    print("\n" + (f"PASS - check_worked_examples: {len(ex)} examples, each tied to the real planner + loops/archetypes/"
                  "planes/tools, descent holds, truth-bearing outputs Baltor-governed."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
