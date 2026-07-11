#!/usr/bin/env python3
"""scripts.check_preference_graph_numeric — PROOF: capability-slot adapter selection is NUMERIC and
non-fragile (owner: "hard-coded roles like candidate/fallback ... better to have a numeric graph of
prioritizations, fallbacks, alternatives ... numeric and non-fragile").

Asserts the preference layer (_repos/baltor/backend/src/baltor/runtime/registry/preference_graph.py):
  A. order is by NUMERIC priority (desc), deterministic tie-break.
  B. explicit numeric priority OVERRIDES the coarse role label (a 'fallback' can outrank a 'primary').
  C. NON-FRAGILE-1: renaming an adapter's provider string does NOT change the order (this is the exact
     fragility that broke check_optimization_harness this session — order depends on numbers, not names).
  D. NON-FRAGILE-2: adding an adapter with an UNKNOWN/missing role does not raise; it sorts to the bottom.
  E. role-derived defaults apply only when no explicit priority is set (gradual migration).
  F. the GRAPH is acyclic: falls_back_to / alternative_of edges with non-negative numeric weights, and the
     order is a monotone-non-increasing chain.
  G. on the REAL catalog: the compression slot ranks headroom(78) > llmlingua(70) > stub(20) — numeric
     preference overriding role labels (llmlingua is role 'primary' yet ranks below the reversible headroom).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.baltor.runtime.registry import preference_graph as pg
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry


def _ids(order):
    return [a["adapter_id"] for a in order]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # A. numeric order
    adapters = [
        {"adapter_id": "a.stub@v1", "role": "stub", "priority": 20, "provider": "Stub"},
        {"adapter_id": "a.high@v1", "role": "fallback", "priority": 90, "provider": "High"},
        {"adapter_id": "a.mid@v1", "role": "primary", "priority": 60, "provider": "Mid"},
    ]
    order = _ids(pg.resolve_order(adapters))
    check("A: ordered by numeric priority desc", order == ["a.high@v1", "a.mid@v1", "a.stub@v1"], str(order))

    # B. explicit priority overrides the role label (fallback@90 beats primary@60)
    check("B: numeric priority overrides the coarse role label",
          order[0] == "a.high@v1" and pg.adapter_priority(adapters[1]) == 90.0)

    # C. NON-FRAGILE-1 — rename providers; order must NOT change (numbers decide, not names)
    renamed = [dict(a, provider=a["provider"] + " / v2-edition (enriched)") for a in adapters]
    check("C: renaming provider strings does NOT change the order", _ids(pg.resolve_order(renamed)) == order,
          str(_ids(pg.resolve_order(renamed))))

    # D. NON-FRAGILE-2 — an UNKNOWN role does not raise; sinks to the bottom (priority 0)
    weird = adapters + [{"adapter_id": "a.weird@v1", "role": "candidate", "provider": "Weird"}]  # 'candidate' is NOT a role
    worder = _ids(pg.resolve_order(weird))
    check("D: unknown role does not crash + sinks to the bottom", worder[-1] == "a.weird@v1", str(worder))
    check("D: unknown/missing role → priority 0", pg.adapter_priority({"role": "candidate"}) == 0.0
          and pg.adapter_priority({}) == 0.0)

    # E. role-derived default when no explicit priority (gradual migration)
    check("E: role-derived default applies absent an explicit priority",
          pg.adapter_priority({"role": "primary"}) == pg.ROLE_DEFAULT_PRIORITY["primary"]
          and pg.adapter_priority({"role": "stub"}) == pg.ROLE_DEFAULT_PRIORITY["stub"])

    # F. graph is acyclic; edges typed by tie-band; order monotone-non-increasing
    g = pg.preference_graph(weird)
    prios = [n["priority"] for n in g["nodes"]]
    check("F: order is monotone non-increasing in priority", all(x >= y for x, y in zip(prios, prios[1:])), str(prios))
    check("F: graph acyclic (all edge weights >= 0)", g["acyclic"] is True)
    check("F: edges are falls_back_to / alternative_of with numeric weight",
          all(e["kind"] in ("falls_back_to", "alternative_of") and isinstance(e["weight"], (int, float)) for e in g["edges"]))
    check("F: top node is the numeric primary", g["primary"] == "a.high@v1", str(g["primary"]))

    # G. REAL catalog: compression slot is numeric, headroom > llmlingua > stub (role label overridden)
    reg = CapabilityRegistry()
    corder = _ids(reg.preference_order("compression"))
    check("G: compression preference order is headroom > llmlingua > stub (numeric over role)",
          corder[:3] == ["compression.headroom@v1", "compression.llmlingua@v1", "compression.stub@v1"], str(corder))
    cg = reg.preference_graph("compression")
    check("G: compression graph is acyclic + primary is headroom (a role='fallback' adapter, by NUMBER)",
          cg["acyclic"] and cg["primary"] == "compression.headroom@v1",
          f"primary={cg['primary']}")

    # H. NUMERIC status codes + edge-type codes (config-sourced; control logic uses numbers, not label strings)
    check("H: status label → numeric code (candidate=30, active=50)",
          pg.status_code({"status": "candidate"}) == 30 and pg.status_code({"status": "active"}) == 50)
    check("H: explicit status_code overrides the label", pg.status_code({"status": "candidate", "status_code": 70}) == 70)
    check("H: unknown status label → 0 (no crash, no string branch)", pg.status_code({"status": "totally-made-up"}) == 0)
    check("H: graph nodes carry numeric status_code", all(isinstance(n.get("status_code"), int) for n in g["nodes"]))
    check("H: graph edges carry a numeric edge_type_code (160 fallback / 120 alternative)",
          all(e.get("edge_type_code") in (120, 160) for e in g["edges"]))

    # determinism
    check("resolve_order is deterministic", _ids(pg.resolve_order(weird)) == _ids(pg.resolve_order(weird)))

    print("\n" + ("PASS — check_preference_graph_numeric: adapter selection is NUMERIC + non-fragile — order "
                  "follows priority numbers (a graph of falls_back_to/alternative_of edges), explicit numbers "
                  "override coarse role labels, renaming providers / unknown roles never break or reorder it, "
                  "and the preference graph is acyclic." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_preference_graph_numeric.py --self-test")
    raise SystemExit(0)
