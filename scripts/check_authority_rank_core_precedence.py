#!/usr/bin/env python3
"""check_authority_rank_core_precedence — proof: the THREE source_type→authority_rank maps (contextops
reliability, contextops source_discovery, graph.temporal.contracts) AND the source_authority registry tiers all
agree on the LOAD-BEARING precedence the moat rests on — source-of-law is the unique top of each map, and
source-of-law > official_agency > agency FAQ — EVEN THOUGH the full maps are not yet value-unified.

Why this exists: the maps drifted to different VALUES (and, for a few low tiers, different ORDER) because each
subsystem maintains its own copy. Fully unifying them is a truth-precedence decision (e.g. is a tenant_document
below or above an agency FAQ? — 15 in reliability vs 50 in discovery) that is OWNER-GATED (OPP-unify-authority-
rank-maps). This gate enforces the part that must NEVER drift regardless of that decision — so a regression that
let a FAQ outrank a regulation in ANY one subsystem fails CI today, without waiting on the owner's numeric call.

CLI: python3 scripts/check_authority_rank_core_precedence.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.artifact_graph.source_authority import _registry
from src.baltor.contextops.authority_rank import AUTHORITY_RANK as SHARED_RANK, scope_adjusted_rank
from src.baltor.contextops.reliability import AUTHORITY_RANK as RELIABILITY_RANK
from src.baltor.contextops.source_discovery import AUTHORITY_RANK as DISCOVERY_RANK
from src.baltor.graph.temporal.contracts import AUTHORITY_RANK as TEMPORAL_RANK

#: every source_type→rank map MUST agree on this chain — the moat's load-bearing precedence.
_CORE_CHAIN = ("source_of_law", "official_agency", "agency_faq")
_MAPS = {"reliability": RELIABILITY_RANK, "source_discovery": DISCOVERY_RANK, "graph.temporal.contracts": TEMPORAL_RANK}
#: registry tiers in their documented strictly-descending order (the artifact-graph authority system).
_TIER_ORDER = ("source_of_law", "official_agency", "official_guidance", "government_other",
               "standards_body", "secondary_summary", "unverified")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    for name, m in _MAPS.items():
        present = [k for k in _CORE_CHAIN if k in m]
        ck(f"{name}: carries the core-chain keys {_CORE_CHAIN}", present == list(_CORE_CHAIN), f"has {present}")
        if present == list(_CORE_CHAIN):
            ranks = [m[k] for k in _CORE_CHAIN]
            ck(f"{name}: source_of_law > official_agency > agency_faq {tuple(ranks)}",
               ranks[0] > ranks[1] > ranks[2])
        top = max(m.values())
        ck(f"{name}: source_of_law is the UNIQUE top of the map",
           m.get("source_of_law") == top and list(m.values()).count(top) == 1,
           f"top={top} source_of_law={m.get('source_of_law')}")

    tiers = _registry()["tiers"]
    tier_ranks = [tiers[t]["rank"] for t in _TIER_ORDER if t in tiers]
    ck("registry tiers strictly descend in the documented order",
       len(tier_ranks) == len(_TIER_ORDER) and all(a > b for a, b in zip(tier_ranks, tier_ranks[1:])), str(tier_ranks))

    # UNIFICATION (A3, 2026-06-18): reliability + source_discovery now read the ONE shared contextops map.
    ck("reliability and source_discovery are the SAME unified map (full equality, not just core chain)",
       RELIABILITY_RANK == DISCOVERY_RANK == SHARED_RANK, f"rel=={RELIABILITY_RANK == SHARED_RANK} disc=={DISCOVERY_RANK == SHARED_RANK}")

    # SCOPE-DEPENDENT PRECEDENCE (A3): a tenant's own doc wins for tenant_private facts, loses for public facts,
    # and never beats an agency's own publication.
    faq, agency = SHARED_RANK["agency_faq"], SHARED_RANK["official_agency"]
    td_private = scope_adjusted_rank("tenant_document", "tenant_private", "tenant_private")
    td_public = scope_adjusted_rank("tenant_document", "tenant_private", "global_public")
    ck("tenant_document OUTRANKS an agency FAQ for a TENANT-PRIVATE fact (scope-aware)", td_private > faq, f"{td_private} vs {faq}")
    ck("tenant_document STAYS BELOW an agency FAQ for a PUBLIC fact (moat preserved)", td_public < faq, f"{td_public} vs {faq}")
    ck("a tenant_document NEVER outranks an agency's own publication, even for its own fact", td_private < agency, f"{td_private} vs {agency}")

    print("  [note] graph.temporal.contracts keeps its own 0..100 tier-scale (different keys); reconciled on the CORE "
          "precedence only — the full crosswalk is OPP-unify-authority-rank-maps step C (owner-gated).")

    print("\n" + ("PASS — check_authority_rank_core_precedence: reliability + source_discovery are UNIFIED onto one "
                  "shared map; the temporal map + registry agree on the load-bearing precedence (source-of-law unique "
                  "top; source-of-law > official_agency > FAQ); and precedence is scope-aware (a tenant's own doc wins "
                  "for tenant_private facts, never for public/regulated ones)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
