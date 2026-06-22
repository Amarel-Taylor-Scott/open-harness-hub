#!/usr/bin/env python3
"""check_external_api_registry — external-API components (RapidAPI/Apify) are real, governed, and credential-mapped.

Owner: some tool components are EXTERNAL APIs (often more deterministic than a browser, e.g. a hosted FB-page scraper).
Proves: every entry maps to a declared plane + a real marketplace credential service (rapidapi/apify) with a key_ownership
model; ToS-sensitive entries (social_scrape / web_unlocker) carry governance; nothing is auto-enabled (candidate/status).
serves_truth=false; discovery≠trust.

  python3 scripts/check_external_api_registry.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    apis = _load("external_api_registry.json")["apis"]
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    cred = {s["id"]: s for s in _load("credential_registry.json")["services"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"external APIs catalogued ({len(apis)})", len(apis) >= 8)
    ck("the owner's FB-page-scrape example is present (governed)",
       any(a["id"] == "fb_page_scrape" and a.get("governance") for a in apis))
    bad_plane = sorted({a["plane"] for a in apis if a["plane"] not in planes})
    ck("every API maps to a declared plane", not bad_plane, str(bad_plane))
    bad_mkt = sorted({a["marketplace"] for a in apis if a["marketplace"] not in cred})
    ck("every API's marketplace is a real credential service", not bad_mkt, str(bad_mkt))
    ck("marketplaces support a key-ownership model (byo/platform/both)",
       all(cred[a["marketplace"]].get("key_ownership") in ("byo", "platform", "both") for a in apis))
    ck("every API declares its own key_ownership", all(a.get("key_ownership") in ("byo", "platform", "both") for a in apis))
    ck("every API declares deterministic + status", all("deterministic" in a and a.get("status") for a in apis))
    # governance on the ToS-sensitive planes
    sensitive = [a for a in apis if a["plane"] == "social_scrape" or a["id"] == "web_unlocker"]
    ck("ToS-sensitive entries (social_scrape / web_unlocker) are governed", all(a.get("governance") for a in sensitive))
    ck("nothing auto-enabled (all candidate, discovery≠trust)", all(a["status"] == "candidate" for a in apis))
    ck("serves_truth=false", _load("external_api_registry.json").get("serves_truth") is False)

    det = sum(1 for a in apis if a["deterministic"])
    print(f"\n  {len(apis)} external-API components ({det} deterministic) across "
          f"{len(set(a['plane'] for a in apis))} planes via {len(set(a['marketplace'] for a in apis))} marketplaces")
    print("\n" + ("PASS - check_external_api_registry: external-API components real, plane+credential-mapped, governed."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
