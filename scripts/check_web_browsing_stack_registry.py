#!/usr/bin/env python3
"""check_web_browsing_stack_registry — the browsing stack registry is valid, governed, license-disciplined, composable.

Proves: >=20 browsers cataloged (target met); driving-components coverage vs the 100+ target is COMPUTED + the gap
surfaced honestly (no filler); license discipline (copyleft/proprietary/unstated/evasion-restricted ⇒ NOT vendorable);
governance (stealth = evasion_restricted, excluded from a default stack; captcha/anti-bot/proxy = guardrail policies
kept); select_stack composes a governed browser+logic+model; the browsers shared with the research catalog agree on
license. serves_truth=false.

  python3 scripts/check_web_browsing_stack_registry.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _self_test() -> int:
    from src.openhubforai.browsing_registry import load_registry, browser_view, coverage, select_stack
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    reg = load_registry()
    cov = coverage(reg)
    ck(f"browsers target MET ({cov['browsers']['have']} >= {cov['browsers']['target']})", cov["browsers"]["met"])
    dc = cov["driving_components"]
    ck(f"driving components seeded ({dc['have']} = {dc['models']} models + {dc['logic']} logic), gap to "
       f"{dc['target']} computed + surfaced (not filler): gap={dc['gap']}", dc["have"] >= 50 and dc["have"] == dc["models"] + dc["logic"])
    ck("coverage counts are COMPUTED from the registry (no magic numbers)",
       cov["browsers"]["have"] == len(reg["browsers"]) and dc["have"] == len(reg["driving_components"]))

    # license discipline (single-source classifier drives vendorable)
    views = {b["id"]: browser_view(b) for b in reg["browsers"]}
    ck("permissive browser is vendorable (playwright/Apache)", views["playwright"]["vendorable"] is True)
    ck("copyleft browser is NOT vendorable (skyvern/AGPL)", views["skyvern"]["vendorable"] is False)
    ck("proprietary browser is NOT vendorable (nova_act)", views["nova_act"]["vendorable"] is False)
    ck("unstated browser is NOT vendorable (webvoyager)", views["webvoyager"]["vendorable"] is False)
    ck("evasion-restricted browser is flagged + NOT vendorable (nodriver)",
       views["nodriver"]["restricted"] is True and views["nodriver"]["vendorable"] is False)

    # governance: every stealth-kind browser is evasion_restricted; guardrail logic policies exist
    stealth = [b for b in reg["browsers"] if b.get("kind") == "stealth"]
    ck("every stealth browser carries governance=evasion_restricted", stealth and all(b.get("governance") == "evasion_restricted" for b in stealth))
    gov_logic = {d["id"] for d in reg["driving_components"] if d.get("subtype") == "governance"}
    ck("guardrail POLICY components present (robots/rate/captcha-refuse/pii)",
       {"robots_txt_compliance", "captcha_policy", "anti_bot_policy", "pii_redaction_on_capture"} <= gov_logic)

    # compose a governed stack
    s = select_stack({"deep_detail", "js_render"}, vendorable_only=True)
    ck("select_stack composes browser + logic + model for deep_detail", s["browser"] and s["logic"] and s["model"])
    ck("vendorable-only stack never picks a copyleft/proprietary/restricted browser",
       s["browser"] not in ("skyvern", "firecrawl", "nova_act", "browserbase", "nodriver", "undetected_chromedriver", "patchright"))
    sv = select_stack({"vision", "interaction"}, vendorable_only=True)
    ck("vision stack selects an OPEN vision/grounding model (vendorable)", sv["model"] in ("qwen2_5_vl", "omniparser", "cogagent", "showui", "uground", "molmo", "internvl", "groundingdino", "paddleocr"))
    ck("a default stack keeps guardrail policies (robots/rate/etc.)", any(g in s["logic"] for g in gov_logic))
    # stealth excluded by default, allowed only when authorized
    s_def = select_stack({"stealth"}, vendorable_only=False, allow_restricted=False)
    s_auth = select_stack({"stealth"}, vendorable_only=False, allow_restricted=True)
    ck("stealth is EXCLUDED by default, available only with allow_restricted", s_def["browser"] is None and s_auth["browser"] is not None)

    # cross-file consistency with the research component catalog (shared browser ids agree on license)
    rcat = json.loads((REPO / "architecture" / "research_component_catalog.json").read_text(encoding="utf-8"))["components"]
    rlic = {c["id"]: c.get("license") for c in rcat if c.get("license")}
    mismatch = [bid for bid, lic in rlic.items() if bid in views and views[bid]["license"] != lic]
    ck("browsers shared with the research catalog agree on license (no drift)", not mismatch, str(mismatch))

    ck("serves_truth=false across the registry", reg.get("serves_truth") is False and cov["serves_truth"] is False)

    print("\n" + (f"PASS - check_web_browsing_stack_registry: {cov['browsers']['have']} browsers (target met) + "
                  f"{dc['have']} driving components ({dc['models']} models + {dc['logic']} logic); coverage gap to "
                  f"{dc['target']} computed + surfaced ({dc['gap']} to fill via intake/discovery); license + governance "
                  "discipline enforced; select_stack composes a governed stack. serves_truth=false." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
