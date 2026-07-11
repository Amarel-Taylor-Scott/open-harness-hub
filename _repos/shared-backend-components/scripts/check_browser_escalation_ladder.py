#!/usr/bin/env python3
"""check_browser_escalation_ladder — the documented browser-method ladder is real, ordered, honest, and ACTUALLY climbed.

Owner: a production tool must NEVER give up at the first wall — document every method + keep trying (headless, headed,
stealth, undetected, vision). Proves: the ladder is cost-ordered with unique rungs; every rung's tools exist in the
browsing registry / tool_registry; statuses are honest (wired vs cataloged); evasion rungs are governed; the WIRED rungs
the code actually climbs (source_search._WIRED_BROWSER_RUNGS) are all present as wired modes in the ladder; and the
higher rungs (undetected/vision/proxy) are cataloged-not-wired (not silently claimed). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_browser_escalation_ladder.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.research import source_search as ss

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _load(name):
    return json.loads((_resource("architecture") / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    lad = _load("browser_escalation_ladder.json")
    rungs = lad["rungs"]
    wbs = _load("web_browsing_stack_registry.json")
    tool_ids = ({b["id"] for b in wbs["browsers"]} | {c["id"] for c in wbs["driving_components"]}
                | {t["id"] for t in _load("tool_registry.json")["tools"]})
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"ladder documents multiple methods ({len(rungs)} rungs)", len(rungs) >= 6)
    ranks = [r["cost_rank"] for r in rungs]
    ck("rungs are cost-ordered, cheapest-first", ranks == sorted(ranks))
    ck("cost_ranks unique", len(set(ranks)) == len(ranks))
    bad_tool = sorted({t for r in rungs for t in r.get("tools", []) if t not in tool_ids})
    ck("every rung's tools exist (browsing registry / tool_registry)", not bad_tool, str(bad_tool))
    ck("statuses honest (wired | cataloged only)", all(r["status"] in ("wired", "cataloged") for r in rungs))
    # evasion rungs (>= stealth) must be governed, never silently used
    evasion = [r for r in rungs if r["cost_rank"] >= 3]
    ck("evasion rungs are governed (robots/ToS / evasion_restricted)", all(r.get("governance") for r in evasion))
    ck("captcha rung never auto-solves (governed high-cost)",
       all("never auto-solve" in r.get("governance", "").lower() or r["id"] != "residential_proxy_or_human" for r in rungs))

    # the code ACTUALLY climbs the wired rungs (not a paper ladder) — and only those + below are 'wired'
    wired_modes = {r["mode"] for r in rungs if r["status"] == "wired"}
    ck("code climbs >1 rung (never stops at rung 1)", len(ss._WIRED_BROWSER_RUNGS) >= 2)
    ck("every mode the code climbs is a WIRED rung in the ladder",
       all(m in wired_modes for m in ss._WIRED_BROWSER_RUNGS), str(set(ss._WIRED_BROWSER_RUNGS) - wired_modes))
    # the strong rungs are cataloged-not-wired (honest about what needs building)
    cataloged = {r["id"] for r in rungs if r["status"] == "cataloged"}
    ck("undetected_driver + vision_coordinate are cataloged (honest, not falsely claimed)",
       {"undetected_driver", "vision_coordinate"} <= cataloged)
    ck("policy states exhaust-before-unavailable", "exhaust" in lad.get("policy", "").lower())
    ck("orthogonal extraction modes documented (selector / a11y / vision-coordinate)",
       set(lad.get("extraction_modes", {})) >= {"by_selector", "by_accessibility", "by_vision_coordinate"})
    ck("serves_truth=false", lad.get("serves_truth") is False)

    print("\n" + (f"PASS - check_browser_escalation_ladder: {len(rungs)} documented rungs, cost-ordered; code climbs "
                  f"{list(ss._WIRED_BROWSER_RUNGS)} then names cataloged rungs. Never gives up at rung 1."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
