#!/usr/bin/env python3
"""check_research_catalog — the research/browse catalog is valid, guarded, and descent-selected (cheapest that works).

Proves the substrate for "hundreds of shared research components, selected efficiently": the catalog is well-formed,
guardrails refuse login-walled hosts, and the descent picks the CHEAPEST eligible component for a needed capability —
escalating to the LLM-driven browser only when it is the only thing that can get the detail, and only when its
resources (browser_runtime + llm) are available and within budget.

  python3 scripts/check_research_catalog.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CONN = REPO / "architecture" / "portfolio_connection_map.json"


def _roster() -> set:
    return {h["name"] for h in json.loads(CONN.read_text(encoding="utf-8")).get("hubs", [])}


def _self_test() -> int:
    from src.openharnesshub.research_catalog import (load_catalog, load_guardrails, host_allowed,
                                                     select_component, descent_plan)
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    comps, tiers = load_catalog()
    g = load_guardrails()
    ids = [c.id for c in comps]
    ck(f"catalog loads ({len(comps)} components across {len(tiers)} tiers)", len(comps) >= 10 and len(tiers) >= 5)
    ck("component ids are unique", len(ids) == len(set(ids)))
    ck("every component has capabilities + a known tier + serves_truth=false",
       all(c.capabilities and c.tier in tiers and c.serves_truth is False for c in comps))
    roster = _roster()
    bad_hub = [c.id for c in comps if c.feeds_hub and c.feeds_hub not in roster]
    ck("every component feeds a real roster hub (recursive: research tools are themselves hub content)", not bad_hub, str(bad_hub))

    # guardrails: login-walled refused, normal allowed
    ck("login-walled host is REFUSED (facebook) — use owner --ingest instead", host_allowed("https://www.facebook.com/x", g)[0] is False)
    ck("a normal host is allowed (api.github.com)", host_allowed("https://api.github.com/repos", g)[0] is True)

    # descent: cheap capability -> cheap component (NOT the browser)
    have_all = {"network", "browser_runtime", "llm", "api_key"}
    sel_list = select_component("list", available=have_all)
    ck("descent picks a CHEAP component for 'list' (feed/api, not browse)", sel_list and tiers[sel_list.tier] <= tiers["api"])
    # deep_detail -> only the LLM-driven browser provides it
    sel_deep = select_component("deep_detail", available=have_all)
    ck("descent escalates to the LLM-driven browser ONLY for deep_detail", sel_deep is not None and sel_deep.id == "llm_driven_browser")
    # browser excluded when its resources aren't available (honest fallback)
    ck("LLM-driven browser NOT selected when browser_runtime/llm unavailable",
       select_component("deep_detail", available={"network"}) is None)
    # browser excluded under a tight cost budget
    ck("LLM-driven browser excluded under a tight budget (escalation is honest, not forced)",
       select_component("deep_detail", available=have_all, budget=3) is None)
    # escalation list is ordered cheapest -> costliest
    plan = descent_plan("text", available=have_all)
    costs = [next(c.cost for c in comps if c.id == cid) for cid in plan["escalation"]]
    ck("escalation order is cheapest -> costliest (try cheap, escalate)", costs == sorted(costs))

    print("\n" + ("PASS - check_research_catalog: research/browse is a governed, descent-selectable catalog — guardrails "
                  "refuse login-walled hosts, the cheapest eligible component is chosen, and the LLM-driven browser is "
                  "selected only when it's the only thing that can get the detail (and is affordable + available). "
                  "serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
