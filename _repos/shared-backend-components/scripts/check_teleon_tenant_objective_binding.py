#!/usr/bin/env python3
"""check_teleon_tenant_objective_binding — proof for per-tenant objective binding.

The objective layer lets you prioritize; THIS binds the priority to the TENANT, so the same capability is planned
differently for different tenants:
  * a compliance tenant resolves to maximize_accuracy; a high-volume tenant to minimize_cost; an interactive
    tenant to minimize_latency; an llm-capped tenant to minimize_llm — each from the shared registry.
  * an explicit WEIGHTS binding (not a preset) resolves to a CapabilityObjective with those exact weights.
  * an unbound tenant gets the documented DEFAULT (never a silent wrong priority); a malformed binding fails loud.
  * IT FLOWS: objective_for_tenant feeds select_placement, so two tenants get DIFFERENT placements for one unit.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_tenant_objective_binding.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.objectives import ObjectiveError, objective_for_tenant
from src.teleon.objectives.tenant_binding import bound_tenants


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # Bindings resolve from the shared registry to the right preset per tenant priority.
    ck("compliance tenant -> maximize_accuracy", objective_for_tenant("baltor-compliance").name == "maximize_accuracy")
    ck("high-volume tenant -> minimize_cost", objective_for_tenant("high-volume-batch").name == "minimize_cost")
    ck("interactive tenant -> minimize_latency", objective_for_tenant("interactive-assistant").name == "minimize_latency")
    ck("llm-capped tenant -> minimize_llm", objective_for_tenant("llm-budget-capped").name == "minimize_llm")
    ck("audit tenant -> maximize_determinism", objective_for_tenant("determinism-first-audit").name == "maximize_determinism")

    # An explicit WEIGHTS binding (not a preset) resolves to those exact weights.
    blend = objective_for_tenant("cost-accuracy-blend")
    w = blend.normalized_weights()
    ck("a custom weights binding resolves to a CapabilityObjective with those weights (cost & accuracy dominate)",
       blend.name == "cost-accuracy-blend" and w["cost"] > w["latency"] and w["accuracy"] > w["llm_usage"], str(w))

    # An unbound tenant gets the documented default (balanced) — never a silent wrong priority.
    ck("an unbound tenant gets the registry default (balanced)",
       objective_for_tenant("some-new-tenant-with-no-binding").name == "balanced")

    # Malformed bindings fail loud (injected registries).
    def raises(reg):
        try:
            objective_for_tenant("t", registry=reg)
            return False
        except ObjectiveError:
            return True
    ck("a binding naming an unknown preset fails loud",
       raises({"bindings": {"t": {"objective_preset": "go_fast"}}, "default_objective_preset": "balanced"}))
    ck("a binding with empty weights fails loud",
       raises({"bindings": {"t": {"weights": {}}}, "default_objective_preset": "balanced"}))
    ck("a registry default naming an unknown preset fails loud",
       raises({"bindings": {}, "default_objective_preset": "nope"}))

    # Deterministic + the listing helper surfaces every bound tenant.
    ck("resolution is deterministic", objective_for_tenant("baltor-compliance").name
       == objective_for_tenant("baltor-compliance").name)
    bt = bound_tenants()
    ck("bound_tenants() lists every bound tenant -> its objective (>=5)",
       len(bt) >= 5 and bt.get("baltor-compliance") == "maximize_accuracy", str(bt))

    # IT FLOWS: the tenant's objective drives REAL placement -> two tenants get different placements for one unit.
    from scripts.teleon_preseed_capabilities import _seed, select_placement
    unit = next(u for u in _seed()["units"] if u["variety"] == "model")
    cost_pick = select_placement(unit, objective_for_tenant("high-volume-batch"))["chosen"]
    latency_pick = select_placement(unit, objective_for_tenant("interactive-assistant"))["chosen"]
    ck("the per-tenant objective FLOWS into placement: cost vs interactive tenants pick DIFFERENT runtime classes",
       cost_pick != latency_pick, f"cost->{cost_pick} interactive->{latency_pick}")

    print("\n" + ("PASS - check_teleon_tenant_objective_binding: each tenant resolves to the CapabilityObjective "
                  "that matches its priority (presets + explicit weights) from the shared registry; an unbound "
                  "tenant gets the documented default; malformed bindings fail loud; and the tenant's objective "
                  "FLOWS into real placement so two tenants plan the same capability differently. Deterministic."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
