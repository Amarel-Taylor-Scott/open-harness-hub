#!/usr/bin/env python3
"""check_optimization_passes — the compiler-pass map is real: each pass binds a real descent axis + an existing module.

Teleon-as-compiler: each optimization pass distills expensive reasoning toward cheap/deterministic/bounded execution
along a descent AXIS. This proves the 10 canonical passes each name a real axis (_repos/shared-backend-components/architecture/descent_method_catalog.json),
every 'have' pass points at a module file that exists (no phantom), the honest engine_gaps are surfaced, and coverage
is computed. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_optimization_passes.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
PASSES = _resource("architecture") / "optimization_passes.json"


def _self_test() -> int:
    data = json.loads(PASSES.read_text(encoding="utf-8"))
    passes = data["passes"]
    axes = {d["axis"] for d in json.loads((_resource("architecture") / "descent_method_catalog.json").read_text(encoding="utf-8"))["dimensions"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"the 10 canonical compiler passes are declared ({len(passes)})", len(passes) >= 10)
    bad_axis = [p["pass"] for p in passes if p.get("axis") not in axes]
    ck("every pass binds a REAL descent axis (descent_method_catalog)", not bad_axis, str(bad_axis))
    missing_mod = [p["pass"] for p in passes if p.get("status") == "have"
                   and not (p.get("module") and (_resource(p["module"])).exists())]
    ck("every 'have' pass points at a module file that exists (no phantom)", not missing_mod, str(missing_mod))
    have = [p["pass"] for p in passes if p["status"] == "have"]
    ck("the core distillation passes are HAVE (deterministic_replacement, model_downgrading, reasoning_distillation, boundary_detection)",
       {"deterministic_replacement", "model_downgrading", "reasoning_distillation", "boundary_detection"} <= set(have))
    ck("the genuine engine GAPS are surfaced honestly (intent→DAG, per-step telemetry, self-rewriting graph)",
       len(data.get("engine_gaps", [])) >= 3 and any("telemetry" in g for g in data["engine_gaps"])
       and any("dag" in g.lower() for g in data["engine_gaps"]))
    ck("serves_truth=false", data.get("serves_truth") is False)

    n_have = len(have)
    n_part = sum(1 for p in passes if p["status"] == "partial")
    print("\n" + (f"PASS - check_optimization_passes: {len(passes)} compiler passes mapped to real descent axes + modules "
                  f"({n_have} have, {n_part} partial); the closed-loop engine gaps (intent→DAG / per-step telemetry / "
                  "self-rewriting graph) surfaced honestly. serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
