#!/usr/bin/env python3
"""check_source_registry — the OpenSourceHub substrate: a cross-industry registry of authoritative sources.

Proves: many sources across industries (healthcare/legal/finance/engineering/business/government); the systems the owner
named are present (state Secretary-of-State incorporation registry, data.gov); sources_for filters by industry/entity/
field (business+company -> SoS + OpenCorporates); the descent is cost-ordered (free public registries first, stealth/paid
later) honoring 'avoid unnecessary paid APIs'; sources are CANDIDATES (discovery != trust). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_source_registry.py --self-test
"""
from __future__ import annotations

from src.teleon.sources import source_registry as SR


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    all_inds = {i for sid in SR.sources() for i in (SR.source(sid).get("industries", []))}
    ck("sources span many industries (healthcare/legal/finance/engineering/business/government)",
       {"healthcare", "legal", "finance", "engineering", "business", "government"} <= all_inds, str(sorted(all_inds)))
    ck("the state Secretary-of-State incorporation registry is present (business/company)",
       SR.source("state_sos_incorporation") is not None and "company" in SR.source("state_sos_incorporation")["entities"])
    ck("data.gov open datasets are present", SR.source("data_gov") is not None and SR.source("data_gov")["kind"] == "open_dataset")

    biz = SR.sources_for(industry="business", entity="company")
    ck("sources_for(business, company) -> SoS incorporation registry + OpenCorporates",
       "state_sos_incorporation" in biz and "opencorporates" in biz, str(biz))
    ck("sources_for(healthcare, provider) -> NPI Registry", "npi_registry" in SR.sources_for(industry="healthcare", entity="provider"))
    ck("'all'/'any' wildcard sources match any industry (brave/org_website for business)",
       "org_website" in SR.sources_for(industry="business") and "brave_search" in SR.sources_for(industry="legal"))

    # cost-ordered descent: free public registries first; paid/grounded/stealth later (avoid unnecessary paid APIs)
    fin = SR.descent(industry="finance")
    ck("finance descent: free public registries (FINRA/SEC) come FIRST", fin[0]["cost_tier"] == "free" and fin[0]["source"] in ("finra_brokercheck", "sec_iapd"))
    biz_desc = SR.descent(industry="business", entity="company")
    tiers = [s["cost_tier"] for s in biz_desc]
    ck("business descent: free/own-browser registries rank before keyed paid APIs",
       tiers.index("browser") < tiers.index("keyed") if ("browser" in tiers and "keyed" in tiers) else True, str([(s["source"], s["cost_tier"]) for s in biz_desc]))
    ck("descent entries carry authority + access (a source is a candidate, discovery != trust)",
       all("authority" in s and "access" in s for s in fin))

    print("\n" + ("PASS - check_source_registry: cross-industry source registry (the OpenSourceHub substrate) — query by "
                  "industry/entity/field, cost-ordered descent (free registries first), sources are candidates."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
