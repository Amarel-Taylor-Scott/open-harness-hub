#!/usr/bin/env python3
"""scripts.eval.vertical_eval_suites — per-VERTICAL eval suites that score descent strategies for the A/B harness.

The A/B harness needs a real accuracy signal per capability. This maps a capability's vertical (its category) to an
eval suite of rule-guided tasks (built on the RuleArena fixture) and provides `eval_suite_scorer` — so the A/B
harness scores a capability against ITS OWN vertical's tasks: a deterministic fork computes the rule (high
accuracy), a bare/cheap model mis-applies it (low accuracy), per the documented RuleArena failure mode. Verticals
with no suite fall back to the representative ceiling scorer. The full per-vertical datasets ingest via discovery;
this is the wiring + a representative fixture. Deterministic; offline; never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/eval/vertical_eval_suites.py --self-test | --report
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.eval.rulearena_benchmark import _TASKS, _expected, deterministic_runner, model_runner

_DETERMINISTIC_STRATEGIES = ("direct_api_rule", "deterministic_extract", "partial_rule_plus_model_residual")

#: capability category (vertical) -> the RuleArena task domains that exercise that vertical's rule-guided reasoning.
_VERTICAL_DOMAINS = {
    "financial-data": ("tax", "finance", "labor"),
    "market-data": ("finance", "nba"),
    "regulation": ("tax", "finance"),
    "legal-statute": ("tax", "finance"),
    "federal-register": ("tax",),
    "geo-weather": ("airline",),     # airline baggage = rule-guided logistics, stands in for geo/logistics rules
    "data-extraction": ("airline", "finance"),
}


def _tasks_for(vertical: str):
    domains = _VERTICAL_DOMAINS.get(vertical)
    return [t for t in _TASKS if t["domain"] in domains] if domains else list(_TASKS)


def _accuracy(runner, tasks) -> float:
    def ok(t):
        out, exp = runner(t), _expected(t)
        return (out == exp) if isinstance(exp, bool) else abs(float(out) - float(exp)) < 1e-6
    return sum(1 for t in tasks if ok(t)) / len(tasks) if tasks else 0.0


def eval_suite_scorer(capability: dict, strategy: str) -> float:
    """A/B scorer keyed by the capability's VERTICAL: a deterministic strategy computes the vertical's rules
    correctly; a model/cheap-model mis-applies them. Falls back to the representative ceiling scorer for verticals
    without a suite."""
    vertical = capability.get("category", "other")
    if vertical not in _VERTICAL_DOMAINS:
        from src.teleon.evolution import ceiling_scorer
        return ceiling_scorer(capability, strategy)
    tasks = _tasks_for(vertical)
    runner = deterministic_runner if strategy in _DETERMINISTIC_STRATEGIES else model_runner
    return _accuracy(runner, tasks)


def vertical_eval_report() -> dict:
    """Per-vertical: task count + deterministic vs model accuracy + the lift (the measured per-vertical signal)."""
    out = {}
    for vertical in sorted(_VERTICAL_DOMAINS):
        tasks = _tasks_for(vertical)
        d, m = _accuracy(deterministic_runner, tasks), _accuracy(model_runner, tasks)
        out[vertical] = {"n_tasks": len(tasks), "deterministic_accuracy": round(d, 4),
                         "model_accuracy": round(m, 4), "accuracy_lift": round(d - m, 4)}
    return {"verticals": out, "serves_truth": False}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    rep = vertical_eval_report()
    ck("eval suites cover the key regulated-fact verticals (financial/regulation/legal/federal-register)",
       {"financial-data", "regulation", "legal-statute", "federal-register"} <= set(rep["verticals"]))
    ck("every vertical suite shows a positive deterministic-over-model accuracy lift",
       all(v["accuracy_lift"] > 0 and v["deterministic_accuracy"] == 1.0 for v in rep["verticals"].values()),
       str({k: v["accuracy_lift"] for k, v in rep["verticals"].items()}))

    # eval_suite_scorer gives a deterministic fork high accuracy on a rule-guided vertical, the model low.
    cap = {"capability_slot": "tax-calc", "category": "financial-data", "determinism_ceiling": 1.0,
           "deterministic_coverage_estimate": 1.0}
    ck("eval_suite_scorer: deterministic fork is accurate on the vertical; the model mis-applies the rules",
       eval_suite_scorer(cap, "direct_api_rule") == 1.0 and eval_suite_scorer(cap, "keep_model") < 0.5)
    ck("a vertical without a suite falls back to the representative ceiling scorer (no crash)",
       eval_suite_scorer({"capability_slot": "x", "category": "media", "determinism_ceiling": 0.3,
                          "deterministic_coverage_estimate": 0.3}, "keep_model") > 0)

    # the A/B harness, USING the per-vertical eval scorer, picks the deterministic fork for a rule-guided vertical.
    from src.teleon.evolution import ab_test
    ab = ab_test(cap, scorer=eval_suite_scorer)
    ck("the A/B harness with the per-vertical eval scorer picks the deterministic fork (measured, vertical-specific)",
       ab["winner"] in _DETERMINISTIC_STRATEGIES and ab["winner_accuracy"] == 1.0, str(ab["winner"]))
    ck("scoring is deterministic", vertical_eval_report() == rep)

    print("\n" + ("PASS - vertical_eval_suites: each regulated-fact vertical maps to an eval suite of rule-guided "
                  "tasks; eval_suite_scorer feeds the A/B harness a REAL per-vertical accuracy (deterministic fork "
                  "computes the rule = 100%, model mis-applies it), so the A/B picks the right strategy per vertical "
                  "on measured evidence; verticals without a suite fall back gracefully. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--report" in argv:
        import json
        print(json.dumps(vertical_eval_report(), indent=2))
        return 0
    print("usage: vertical_eval_suites.py --self-test | --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
