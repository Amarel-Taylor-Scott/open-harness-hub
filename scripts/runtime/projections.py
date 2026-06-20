#!/usr/bin/env python3
"""scripts.runtime.projections — disposable, rebuildable hot-query projections over the canonical ledger.

The canonical artifact ledger (long/narrow + JSON payload + content_hash) is the source of truth and stays
flexible — new artifact types need NO schema migration. Frequently-queried shapes (facts, vectors, entities,
conflicts) are PROJECTIONS derived from the ledger; they can be dropped and rebuilt at any time. This proves
the hybrid model: flexible canonical store + fast disposable projections.
"""
from __future__ import annotations


def build_fact_projection(ledger, tenant_id: str) -> list[dict]:
    """Rebuild a promotable-fact projection from the canonical ledger."""
    return [{"artifact_id": a["artifact_id"], "promotion_eligible": a["promotion_eligible"], "run_id": a["run_id"]}
            for a in ledger.artifacts(tenant_id, "atomic_fact")]


def build_type_projection(ledger, tenant_id: str) -> dict[str, int]:
    """Rebuild the artifact-count-by-type projection (analytics)."""
    return dict(ledger.counts_by_type(tenant_id))


def build_vector_projection(ledger, tenant_id: str) -> list[dict]:
    return [{"artifact_id": v["artifact_id"], "provider": v["vector_provider"], "dims": v["dimensions"]}
            for v in ledger.vectors(tenant_id)]
