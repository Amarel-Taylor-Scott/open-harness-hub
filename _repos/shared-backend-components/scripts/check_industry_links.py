#!/usr/bin/env python3
"""check_industry_links — the per-industry linking-rules surface (the OpenLinkingHub substrate).

Proves: many industries are registered (healthcare/legal/finance/engineering/real_estate/accounting; insurance excluded);
ruleset_for maps each entity role to the right entity-resolution ruleset (provider->person, practice->organization,
location->address); resolve_role dedups a role using that ruleset; link() applies cross-entity linkage (a provider is
affiliated_with a practice when practice_name~name + address agree) — and the SAME surface links an attorney to a firm by
swapping only the industry. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_industry_links.py --self-test
"""
from __future__ import annotations

from src.teleon.resolution import industry_links as IL


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    inds = IL.industries()
    ck("many industries registered (healthcare/legal/finance/engineering/real_estate/accounting)",
       {"healthcare", "legal", "finance", "engineering", "real_estate", "accounting"} <= set(inds))
    ck("INSURANCE is excluded (non-compete)", IL.industry("insurance") is None)
    ck("ruleset_for maps roles to entity-resolution rulesets (provider->person, practice->organization, location->address)",
       IL.ruleset_for("healthcare", "provider") == "person" and IL.ruleset_for("healthcare", "practice") == "organization" and IL.ruleset_for("healthcare", "location") == "address")

    # resolve a role's records using that industry+role's ruleset (dedup practices via the organization ruleset)
    practices = [{"id": "PR1", "name": "ABC Heart Group LLC", "address": "100 Main St"},
                 {"id": "PR2", "name": "ABC Heart Grp, Inc.", "address": "100 Main Street"},   # dup of PR1
                 {"id": "PR3", "name": "XYZ Cardiology Center", "address": "9 Oak Ave"}]
    rr = IL.resolve_role("healthcare", "practice", practices)
    clusters = {frozenset(c) for c in rr["entities"]}
    ck("resolve_role dedups practices via the organization ruleset (PR1,PR2 cluster; PR3 distinct)",
       frozenset({"PR1", "PR2"}) in clusters and frozenset({"PR3"}) in clusters, str(rr["entities"]))

    # cross-entity LINKAGE: a provider affiliated_with a practice (practice_name~name + address)
    hc = IL.link("healthcare", {
        "provider": [{"provider_id": "DR1", "name": "Robert Smith", "practice_name": "ABC Heart Group", "address": "100 Main St"}],
        "practice": [{"id": "PR1", "name": "ABC Heart Group LLC", "address": "100 Main St"}, {"id": "PR3", "name": "XYZ Cardiology", "address": "9 Oak Ave"}],
    })
    aff = [l for l in hc["links"] if l["type"] == "affiliated_with"]
    ck("link(): provider DR1 affiliated_with practice PR1 (name + address agree), NOT PR3",
       any(l["from_id"] == "DR1" and l["to_id"] == "PR1" for l in aff) and not any(l["to_id"] == "PR3" for l in aff), str(aff))

    # the SAME surface, different industry: attorney -> firm, by swapping only the industry
    lg = IL.link("legal", {
        "attorney": [{"id": "A1", "name": "Jane Roe", "firm_name": "Roe and Partners", "address": "1 Plaza"}],
        "firm": [{"id": "F1", "name": "Roe & Partners LLP", "address": "1 Plaza"}],
    })
    ck("SAME surface, LEGAL industry: attorney A1 affiliated_with firm F1 (firm_name~name + address)",
       any(l["from_id"] == "A1" and l["to_id"] == "F1" for l in lg["links"]), str(lg["links"]))

    ck("an unknown/excluded industry is an honest error", "error" in IL.link("insurance", {}))
    ck("serves_truth=false", hc["serves_truth"] is False and rr["serves_truth"] is False)

    print("\n" + ("PASS - check_industry_links: per-industry linking surface — role->ruleset + cross-entity linkage, the "
                  "same engine across healthcare/legal/finance/…; insurance excluded." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
