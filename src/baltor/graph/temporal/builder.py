"""src.baltor.graph.temporal.builder — build the governed temporal graph from observations, and the CFPB
reference case end-to-end. Records reconciliation/verification as edges + receipts; never serves truth itself.
"""
from __future__ import annotations

from .contracts import content_hash, EPOCH, VERIFIED_CURRENT, HELD_OUT
from .store import TemporalGraphStore
from .policy import project_current

_VERIFIED_KEY = "reg_e.error_resolution.deadline"
_VERIFIED_ANSWER = "10 business days"
_HELD_OUT_ANSWER = "30 days"


def _receipt(op: str, tenant_id: str, node_ids: list, edge_ids: list, *, now: str = EPOCH) -> dict:
    body = {"op": op, "tenant_id": tenant_id, "node_ids": sorted(node_ids), "edge_ids": sorted(edge_ids)}
    return {"schema_version": "TemporalGraphReceipt.v1", "receipt_id": "tgr-" + content_hash(body)[7:27],
            "op": op, "tenant_id": tenant_id, "node_ids": sorted(node_ids), "edge_ids": sorted(edge_ids),
            "policy_id": "authority_then_freshness", "created_at": now, "content_hash": content_hash(body)}


def build_cfpb_temporal_graph(store: TemporalGraphStore | None = None, *, tenant_id: str = "global",
                              now: str = "2026-06-06T00:00:00Z", recon_receipt_id: str = "recon-cfpb-regE-10",
                              verify_receipt_id: str = "verify-cfpb-regE-10") -> dict:
    """Build the CFPB temporal graph: Reg E '10 business days' (source_of_law) becomes verified_current;
    FAQ '30 days' (official_faq) is held out (preserved). Writes CONTRADICTS / HELD_OUT_BY / RECONCILED_BY /
    VERIFIED_BY / CURRENT_VERSION_OF edges. Records the EXISTING reconciliation decision (assert-equivalence)."""
    store = store or TemporalGraphStore()
    rege = store.add_observation(
        canonical_fact_key=_VERIFIED_KEY, tenant_id=tenant_id, scope="global_public",
        subject="error_resolution", predicate="deadline", obj=_VERIFIED_ANSWER, value_normalized=_VERIFIED_ANSWER,
        unit="business_days", source_authority="source_of_law", source_handles=["ctx://reg-e/1693f#1005.11"],
        source_artifact_ids=["art_reg_e_10"], now=now, claim_status="atomic_fact")
    faq = store.add_observation(
        canonical_fact_key=_VERIFIED_KEY, tenant_id=tenant_id, scope="global_public",
        subject="error_resolution", predicate="deadline", obj=_HELD_OUT_ANSWER, value_normalized=_HELD_OUT_ANSWER,
        unit="days", source_authority="official_faq", source_handles=["ctx://cfpb-faq/sec-3#deadline"],
        source_artifact_ids=["art_faq_30"], now=now, claim_status="atomic_fact")

    # governed projection: source-of-law wins, FAQ held out (writes CONTRADICTS)
    state = project_current(store, canonical_fact_key=_VERIFIED_KEY, tenant_id=tenant_id, now=now, write_edges=True)

    edges = []
    # record the reconciliation + verification as edges + receipts (graph RECORDS, does not decide)
    edges.append(store.add_edge(tenant_id=tenant_id, from_id=faq.temporal_fact_id, to_id=rege.temporal_fact_id,
                 edge_type="HELD_OUT_BY", edge_source="deterministic", receipt_id=recon_receipt_id,
                 policy_id="source_of_law_beats_faq", policy_version="v1", observed_at=now,
                 evidence_json={"loser": _HELD_OUT_ANSWER, "winner": _VERIFIED_ANSWER}))
    edges.append(store.add_edge(tenant_id=tenant_id, from_id=rege.temporal_fact_id, to_id=faq.temporal_fact_id,
                 edge_type="RECONCILED_BY", edge_source="deterministic", receipt_id=recon_receipt_id,
                 policy_id="source_of_law_beats_faq", policy_version="v1", observed_at=now))
    edges.append(store.add_edge(tenant_id=tenant_id, from_id=rege.temporal_fact_id, to_id=rege.temporal_fact_id,
                 edge_type="VERIFIED_BY", edge_source="deterministic", receipt_id=verify_receipt_id, observed_at=now))
    edges.append(store.add_edge(tenant_id=tenant_id, from_id=rege.temporal_fact_id, to_id=rege.temporal_fact_id,
                 edge_type="CURRENT_VERSION_OF", edge_source="deterministic", observed_at=now,
                 evidence_json={"canonical_fact_key": _VERIFIED_KEY}))
    # stamp receipts on the winner node
    rege.verification_receipt_ids.append(verify_receipt_id)
    rege.reconciliation_receipt_ids.append(recon_receipt_id)
    faq.reconciliation_receipt_ids.append(recon_receipt_id)

    receipt = _receipt("graph.temporal.build.cfpb", tenant_id, [rege.temporal_fact_id, faq.temporal_fact_id],
                       [e["edge_id"] for e in edges], now=now)
    return {"store": store, "state": state, "current_node": rege.to_dict(), "held_out_node": faq.to_dict(),
            "edges": store.edges(tenant_id), "receipt": receipt, "tenant_id": tenant_id,
            "fact_key": _VERIFIED_KEY, "reference_answer": _VERIFIED_ANSWER, "held_out_answer": _HELD_OUT_ANSWER}
