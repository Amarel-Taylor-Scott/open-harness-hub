#!/usr/bin/env python3
"""check_teleon_objective_gated_descent — proof that a CapabilityObjective GOVERNS a unit's self-improvement.

demonstrate_descent proves the model -> distilled-rule descent fires on the real adapt() engine; THIS proves the
objective DECIDES whether it should. The objective scores the model vs its distilled deterministic rule:
  * cost / determinism / llm objectives -> DESCEND: Teleon runs the REAL adapt() engine and promotes the cheap
    deterministic rule, keeping the model as a reversible rollback_target (the cost self-improvement).
  * a maximize_accuracy objective, WHEN the rule diverges on held-out/novel inputs -> HOLD: Teleon vetoes the
    descent and keeps the model (consistent with the lossless-distillation law — never trade answer-critical
    accuracy for cost). With NO divergence (the rule is equivalent), even maximize_accuracy descends.
So the SAME descent either fires or is vetoed purely by the priority — flexible, traceable, never serving truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_objective_gated_descent.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.teleon_preseed_capabilities import objective_gated_descent
from src.teleon.objectives import PRESETS


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # cost / determinism / llm priorities -> the descent FIRES on the real adapt() engine.
    for obj in ("minimize_cost", "maximize_determinism", "minimize_llm"):
        d = objective_gated_descent(PRESETS[obj])
        ck(f"{obj}: DESCENDS — promotes the distilled deterministic rule (real adapt() engine)",
           d["decision"] == "descend" and d["promoted"] is True
           and d["after_impl"].startswith("distilled_rule") and d["before_impl"].startswith("model"),
           str({k: d.get(k) for k in ("decision", "promoted", "after_impl")}))
        ck(f"{obj}: the descent is cost-reducing and keeps the model as a reversible rollback_target",
           d["after_cost"] < d["before_cost"] and bool(d["rollback_target"])
           and d["rollback_target"].startswith("model") and d["equivalent"] is True)

    # maximize_accuracy WHEN the rule diverges on novel/held-out inputs -> the objective VETOES the descent.
    held = objective_gated_descent(PRESETS["maximize_accuracy"], novel_divergence=True)
    ck("maximize_accuracy + novel divergence: HOLDS — keeps the model, does NOT promote the rule",
       held["decision"] == "hold" and held["promoted"] is False and held["selection"]["chosen"] == "model",
       str({k: held.get(k) for k in ("decision", "promoted")}))
    ck("the held-back descent carries a traceable reason (why the objective vetoed it)", bool(held.get("held_reason")))

    # maximize_accuracy WITH NO divergence (rule is equivalent) -> even accuracy lets the descent fire.
    equiv = objective_gated_descent(PRESETS["maximize_accuracy"], novel_divergence=False)
    ck("maximize_accuracy + NO divergence: DESCENDS — an equivalent rule is promoted even under accuracy priority",
       equiv["decision"] == "descend" and equiv["promoted"] is True, str({k: equiv.get(k) for k in ("decision", "promoted")}))

    # the decision is traceable (scores both impls + weights), never serves truth, and is deterministic.
    t = objective_gated_descent(PRESETS["minimize_cost"])["selection"]
    ck("the gating decision is a full SelectionTrace (both impls scored + weights + rationale)",
       len(t["ranked"]) == 2 and {r["impl_id"] for r in t["ranked"]} == {"model", "distilled_rule"}
       and bool(t["rationale"]) and bool(t["weights"]))
    ck("the gating decision never serves truth", t["serves_truth"] is False
       and objective_gated_descent(PRESETS["maximize_accuracy"], novel_divergence=True)["serves_truth"] is False)
    ck("the gating decision is deterministic (same objective+divergence -> same decision)",
       objective_gated_descent(PRESETS["maximize_accuracy"], novel_divergence=True)["decision"]
       == objective_gated_descent(PRESETS["maximize_accuracy"], novel_divergence=True)["decision"])

    print("\n" + ("PASS - check_teleon_objective_gated_descent: a CapabilityObjective GOVERNS a unit's non-det -> "
                  "det descent — cost/determinism/llm priorities fire the real adapt() promotion (cheaper, "
                  "equivalent, model kept as rollback_target); a maximize_accuracy priority VETOES the descent when "
                  "the distilled rule diverges on novel/held-out inputs (and lets it fire when the rule is "
                  "equivalent). The same descent fires or is held purely by the priority — traceable, deterministic, "
                  "never serving truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
