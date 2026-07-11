#!/usr/bin/env python3
"""check_teleon_unit_placement — proof that a CapabilityObjective drives REAL placement on the seeded units.

objective.py proves the selection MECHANISM on a synthetic candidate set; THIS proves it on the ACTUAL
pre-seeded capability units: every unit's REAL allowed_runtime_classes become objective candidates measured by
REAL pricebook cost (production = cloud where the class runs on cloud, else the local floor) + the REAL SLA
latency budget parsed from each runtime profile. A tighter SLA generally costs more, so "prioritize latency" and
"prioritize cost" pick DIFFERENT, sane placements per unit — each with the objective layer's full, deterministic,
never-truth SelectionTrace. This is the flexibility layer made REAL on the units, not a synthetic demo.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_unit_placement.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.teleon_preseed_capabilities import _seed, _sla_seconds, resolve_resources, select_placement
from src.teleon.objectives import PRESETS


def _placement_cost(r: dict) -> float:
    """The same production-cost rule select_placement uses: cloud cost where the class runs on cloud, else local."""
    return float(r["cloud_cost"] if r["cloud_cost"] is not None else r["local_cost"])


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    units = _seed()["units"]

    # The latency budget is PARSED from the declared SLA id (single-sourced from the profile) — never re-typed.
    ck("SLA latency budget parses from the declared policy id (30s->30, 2m->120, 24h->86400)",
       _sla_seconds("interactive_30s") == 30 and _sla_seconds("standard_2m") == 120
       and _sla_seconds("offline_24h") == 86400)
    ck("an SLA id with no parseable duration falls back to a neutral budget (never crashes)",
       _sla_seconds("weird_policy") == 120.0 and _sla_seconds(None) == 120.0)

    flips = 0
    for u in units:
        v = u["variety"]
        runtime = resolve_resources(u)["runtime"]
        rcs = [r["runtime_class"] for r in runtime]
        budgets = {r["runtime_class"]: _sla_seconds(r["sla_policy"]) for r in runtime}
        costs = {r["runtime_class"]: _placement_cost(r) for r in runtime}

        lat = select_placement(u, PRESETS["minimize_latency"])
        cost = select_placement(u, PRESETS["minimize_cost"])

        # TRACEABILITY: every allowed runtime class is scored; the choice is one of them; never served truth.
        ck(f"{v}: placement trace scores every allowed runtime class + never serves truth",
           len(lat["ranked"]) == len(rcs) and lat["chosen"] in rcs and lat["serves_truth"] is False
           and bool(lat["rationale"]) and all("score" in r for r in lat["ranked"]))
        # minimize_latency -> the tightest-SLA runtime class (the clear, useful latency lever).
        ck(f"{v}: minimize_latency picks the tightest-SLA runtime class",
           budgets[lat["chosen"]] == min(budgets.values()), f"{lat['chosen']} {budgets}")
        # minimize_cost -> a minimum production-cost runtime class.
        ck(f"{v}: minimize_cost picks a minimum-cost runtime class",
           costs[cost["chosen"]] == min(costs.values()), f"{cost['chosen']} {costs}")
        if lat["chosen"] != cost["chosen"]:
            flips += 1

    # FLEXIBILITY: most units genuinely flip placement between latency-first and cost-first priorities.
    ck("the SAME units choose DIFFERENT placements under latency-vs-cost priorities (real flexibility)",
       flips >= 3, f"flips={flips}/{len(units)}")

    # DETERMINISTIC
    u0 = units[0]
    ck("placement is deterministic (same unit + objective -> identical trace)",
       select_placement(u0, PRESETS["minimize_latency"]) == select_placement(u0, PRESETS["minimize_latency"]))

    print("\n" + ("PASS - check_teleon_unit_placement: every pre-seeded unit's REAL allowed runtime classes are "
                  "scored by a CapabilityObjective using REAL pricebook cost + the REAL SLA latency budget; "
                  "minimize_latency picks the tightest-SLA placement and minimize_cost the cheapest, so the same "
                  "units flip placement under different priorities — the flexibility layer applied to the actual "
                  "units, deterministic and never serving truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
