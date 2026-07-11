"""contextops/authority_rank — the ONE canonical source_type→authority_rank map + SCOPE-AWARE precedence.

Previously three subsystems each kept their own divergent copy of this map (contextops reliability, contextops
source_discovery, and graph.temporal.contracts), with the same "single source" comment on each. This module is
the single source for the **contextops source_type scale**: ``reliability`` and ``source_discovery`` import it;
the temporal graph keeps its own 0..100 tier-scale in ``graph.temporal.contracts`` (different keys), held to the
shared CORE precedence by ``_repos/shared-backend-components/scripts/check_authority_rank_core_precedence.py``.

SCOPE-DEPENDENT PRECEDENCE (owner-ratified 2026-06-18, A3): authority is EARNED, but a tenant's OWN document is
authoritative for that tenant's OWN (tenant_private) facts. So precedence is scope-aware:
  - **public / regulated facts** → official sources win; a ``tenant_document`` stays at its LOW base rank (the
    earned-authority moat: an internal doc never overrides a regulated public fact).
  - **tenant_private facts** → a ``tenant_private`` source is promoted ABOVE the public-interpretive tiers
    (agency FAQ / vendor doc / dataset) for THAT fact — it can never beat binding source-of-law / a regulation /
    an agency's own publication, but it outranks a generic public FAQ for the tenant's own internal fact.
Deterministic, stdlib-only, no clock.
"""
from __future__ import annotations

#: canonical default authority_rank per source_type (higher outranks lower). Single source for the contextops
#: scale — imported by reliability + source_discovery. source-of-law > regulation > statute > official_agency >
#: primary_dataset > agency_faq > vendor_doc > secondary_summary > tenant_document > blog.
AUTHORITY_RANK: dict[str, int] = {
    "source_of_law": 95,
    "regulation": 90,
    "statute": 88,
    "official_agency": 80,
    "primary_dataset": 70,
    "agency_faq": 30,
    "vendor_doc": 25,
    "secondary_summary": 20,
    "tenant_document": 15,
    "blog": 5,
}
#: PRIOR per-map values preserved for lineage (lossless — this map unified them onto the reliability scale on
#: 2026-06-18): source_discovery formerly had vendor_doc=40, agency_faq=20, secondary_summary=15,
#: tenant_document=50; graph.temporal.contracts keeps its own tier-scale (source_of_law=100, +official_api/
#: public_summary/etc.) and is reconciled only on the CORE chain, not value-unified.
_PRIOR_DISCOVERY_RANKS = {"vendor_doc": 40, "agency_faq": 20, "secondary_summary": 15, "tenant_document": 50}

#: the rank a tenant_private source is treated AS when it backs a tenant_private fact: just below official_agency
#: (80), so it outranks the public-interpretive tiers (primary_dataset/FAQ/vendor) for the tenant's own fact, but
#: never an agency's own publication or binding law. Owner-tunable (this is the A3 promotion level).
TENANT_PRIVATE_EFFECTIVE_RANK = 79


def default_authority_rank(source_type: str) -> int:
    """The scope-INDEPENDENT comparative authority for a source_type (source-of-law > FAQ). Unknown → 0."""
    return AUTHORITY_RANK.get(source_type, 0)


def scope_adjusted_rank(source_type: str, source_scope: str = "global_public",
                        fact_scope: str | None = None) -> int:
    """The SCOPE-AWARE authority_rank used for precedence (A3). For a tenant_private fact backed by a
    tenant_private source, promote it to ``TENANT_PRIVATE_EFFECTIVE_RANK`` (above public-interpretive tiers,
    below official/binding tiers) — a tenant's own doc is authoritative for its own fact. Otherwise the base
    rank stands (official sources win for public/regulated facts; the earned-authority moat is unchanged)."""
    base = default_authority_rank(source_type)
    if fact_scope == "tenant_private" and source_scope == "tenant_private":
        return max(base, TENANT_PRIVATE_EFFECTIVE_RANK)
    return base


__all__ = ["AUTHORITY_RANK", "TENANT_PRIVATE_EFFECTIVE_RANK", "default_authority_rank", "scope_adjusted_rank"]
