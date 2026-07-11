#!/usr/bin/env python3
"""check_self_optimizing_unit — proof for the self-improving, auto-optimizing Teleon capability unit: it measures
itself and auto-applies the best GOVERNED method per dimension (compress tokens, distill to a deterministic rule
or a cheaper model, bind a fragile fact to its source, route to the cheapest capable model), emitting a real
before→after receipt. Governed throughout (lossless, within policy, accuracy-floored, serves_truth=false) and
HONEST: an open-ended capability gets a cheaper model (cost↓) but is NOT falsely made deterministic.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_self_optimizing_unit.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.self_optimizing_unit import SelfOptimizingCapabilityUnit, demonstrate

_FRAGILE = {  # a regulated fact: distillable to a deterministic rule + needs freshness
    "slot": "reg-e-deadline", "category": "identity-compliance", "determinism_ceiling": 0.95,
    "deterministic_coverage_estimate": 0.9, "authoritative_source": "ecfr://12/1005.11", "volatility_class": "low",
    "skill_text": "Do X.\nDo X.\n[optional] greet the user.\nCite the authoritative source.", "must_keep": ("authoritative source",),
}
_OPEN_ENDED = {  # an open-ended text task: CANNOT be made deterministic; the honest win is a cheaper model
    "slot": "summarize-regulation-change", "category": "research", "determinism_ceiling": 0.3,
    "deterministic_coverage_estimate": 0.4,
    "skill_text": "Summarize the change.\nSummarize the change.\n[optional] add flair.", "must_keep": (),
}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = SelfOptimizingCapabilityUnit(_FRAGILE).optimize()
    dims = set(r["dimensions_improved"])
    steps = {st["dimension"]: st for st in r["steps"]}

    ck("the unit auto-optimizes across MULTIPLE dimensions (>= 4)", len(dims) >= 4, str(sorted(dims)))
    ck("tokens_in: compression reduces input tokens (after < before)",
       steps["tokens_in"]["after"] < steps["tokens_in"]["before"])
    ck("cost: distillation lowers per-call cost", steps["cost"]["after"] < steps["cost"]["before"])
    ck("determinism: a distillable regulated fact reaches deterministic 1.0",
       "determinism" in steps and steps["determinism"]["after"] == 1.0)
    ck("freshness: a fragile fact's stale-served risk is driven to 0 (held out)",
       "freshness" in steps and steps["freshness"]["after"] == 0.0)
    ck("efficiency: routes to a cheaper capable model than the frontier worst-case",
       "efficiency" in steps and steps["efficiency"]["after"] < steps["efficiency"]["before"])
    ck("every applied fork is GOVERNED (lossless + within policy = accuracy floor respected)",
       r["accuracy_floor_respected"] is True and all(st["governed"] for st in r["steps"]))
    ck("the unit creates a lineage of forks (lossless evolution graph)", len(r["lineage_forks"]) >= 2)
    ck("the unit never serves truth (it PROPOSES; a gate disposes)", r["serves_truth"] is False)

    # HONESTY: an open-ended task gets a cheaper model (cost↓) but is NOT falsely made deterministic
    ro = SelfOptimizingCapabilityUnit(_OPEN_ENDED).optimize()
    odims = set(ro["dimensions_improved"])
    ck("open-ended capability: cost still improves (cheaper model)", "cost" in odims)
    ck("open-ended capability: NOT falsely made deterministic (honest — determinism is impossible here)",
       "determinism" not in odims)

    # idempotent / deterministic convergence (auto-optimization settles)
    ck("auto-optimization is deterministic + idempotent (re-optimize → identical receipt)",
       SelfOptimizingCapabilityUnit(_FRAGILE).is_converged() and SelfOptimizingCapabilityUnit(_FRAGILE).optimize() == r)

    ck("the demonstrate() capstone runs and improves >= 5 dimensions (the flagship)",
       len(demonstrate()["dimensions_improved"]) >= 5)

    print("\n" + (f"PASS - check_self_optimizing_unit: the capability unit auto-optimizes itself across "
                  f"{len(dims)} dimensions (tokens↓ / cost↓ / determinism↑ / fragility→freshness / efficiency↑) with "
                  f"real governed before→after numbers — lossless, within policy, accuracy-floored, never serving "
                  f"truth; honest when a task can't be made deterministic (cheaper model instead); deterministic + "
                  f"idempotent. The self-improving Teleon unit." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_self_optimizing_unit.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
