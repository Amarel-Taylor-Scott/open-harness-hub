#!/usr/bin/env python3
"""check_inefficient_pipeline_archetypes — the waste-pattern taxonomy + the optimization heuristic library are real.

Proves: each of the 12 inefficient-pipeline archetypes maps to real agentic loops (agentic_loop_catalog), real fixing
passes (optimization_passes), and declared replacement planes (tool_planes); and each IF-THEN heuristic references a real
archetype + real passes. This is the seed of the Cognition→Deterministic-replacement knowledge graph (the brain learns
more from traces). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_inefficient_pipeline_archetypes.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _load(name):
    return json.loads((_resource("architecture") / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    arch = _load("inefficient_pipeline_archetypes.json")["archetypes"]
    heur = _load("optimization_heuristics.json")["heuristics"]
    loops = {L["id"] for L in _load("agentic_loop_catalog.json")["loops"]}
    passes = {p["pass"] for p in _load("optimization_passes.json")["passes"]}
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    arch_ids = {a["id"] for a in arch}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"12 inefficient-pipeline archetypes declared ({len(arch)})", len(arch) >= 12)
    bad_loop = sorted({L for a in arch for L in a.get("loops", []) if L not in loops})
    ck("every archetype's loops are real (agentic_loop_catalog)", not bad_loop, str(bad_loop))
    bad_pass = sorted({p for a in arch for p in a.get("passes", []) if p not in passes})
    ck("every archetype's fixing passes are real (optimization_passes)", not bad_pass, str(bad_pass))
    bad_plane = sorted({pl for a in arch for pl in a.get("planes", []) if pl not in planes})
    ck("every archetype's replacement planes are declared (tool_planes)", not bad_plane, str(bad_plane))
    ck("every archetype names example deterministic primitives", all(a.get("primitives") for a in arch))

    ck(f"optimization heuristic library seeded ({len(heur)} IF-THEN rules)", len(heur) >= 8)
    bad_h_arch = [h["id"] for h in heur if h.get("archetype") not in arch_ids]
    ck("every heuristic references a real archetype", not bad_h_arch, str(bad_h_arch))
    bad_h_pass = sorted({p for h in heur for p in h.get("then", []) if p not in passes})
    ck("every heuristic's THEN-passes are real", not bad_h_pass, str(bad_h_pass))
    ck("every heuristic has a when-condition + concrete actions", all(h.get("when") and h.get("actions") for h in heur))
    ck("serves_truth=false (candidate heuristics; nothing auto-applies without sandbox + guardrails)",
       _load("inefficient_pipeline_archetypes.json").get("serves_truth") is False
       and _load("optimization_heuristics.json").get("serves_truth") is False)

    print("\n" + (f"PASS - check_inefficient_pipeline_archetypes: {len(arch)} waste archetypes mapped to real loops/passes/"
                  f"planes + {len(heur)} IF-THEN heuristics (the seed of the cognition→deterministic knowledge graph). "
                  "serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
