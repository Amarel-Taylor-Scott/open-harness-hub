#!/usr/bin/env python3
"""check_provider_sources — the 'search trusted sources' rung as a cost-ordered descent (avoid unnecessary paid APIs).

Proves: the source ladder is cost-ordered (free public registries first, stealth last); for a field free registries cover
(address), the plan uses NO paid API; for a field they don't (website), it climbs to your OWN browser BEFORE a paid API;
max_cost_tier caps the climb; fetch is honest-offline and a keyed source honestly reports it needs a credential. serves_truth=false.

  python3 scripts/check_provider_sources.py --self-test
"""
from __future__ import annotations

from src.teleon.verticals import provider_sources as PS


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ladder = PS.source_ladder()
    ck("ladder is cost-ordered: a FREE public registry first, stealth last",
       ladder[0]["cost_tier"] == "free" and ladder[-1]["id"] == "stealth_browser", f"{ladder[0]['id']}..{ladder[-1]['id']}")
    ck("NPI Registry (free, authoritative) is the rung-0 source", ladder[0]["id"] in ("npi_registry", "cms"))

    # address is covered by FREE registries -> the plan must NOT include a paid API
    addr = PS.plan_acquisition(["address"])
    addr_sources = [s["source"] for s in addr["plan"][0]["sources"]]
    ck("a field free registries cover (address) -> plan uses ONLY free registries, no paid API",
       all(s in ("npi_registry", "cms") for s in addr_sources) and addr_sources, str(addr_sources))

    # website is NOT in the free registries -> climb to your OWN browser BEFORE a paid API
    web_ladder = [r["id"] for r in PS.source_ladder("website")]
    ck("for website: own browser (practice_website) ranks BEFORE paid search (brave/serpapi)",
       web_ladder.index("practice_website") < min(web_ladder.index("brave_search"), web_ladder.index("serpapi")))

    # max_cost_tier caps the climb (free-only never reaches browser/paid/stealth)
    cap = PS.plan_acquisition(["website"], max_cost_tier="free")
    ck("max_cost_tier='free' caps the climb (no browser/paid/stealth attempted for website)", cap["plan"][0]["sources"] == [] and not cap["plan"][0]["covered"])

    # fetch: honest-offline, keyed needs a key, unknown is honest
    ck("fetch is honest-offline (no fabricated source data)", PS.fetch("npi_registry", "Dr X Naples FL", network_allowed=False)["available"] is False)
    keyed = PS.fetch("brave_search", "ABC Heart Group Naples", network_allowed=True)
    ck("a KEYED source honestly reports it needs a credential", keyed["available"] is False and keyed.get("needs_key") is True)
    ck("an unknown source is honest (not fabricated)", PS.fetch("not_a_source", "x")["available"] is False)
    ck("serves_truth=false", addr["serves_truth"] is False)

    print("\n" + ("PASS - check_provider_sources: cost-ordered source descent — free public registries first, own browser "
                  "before paid APIs, stealth last; honest-offline + keyed-needs-key." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
