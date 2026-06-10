"""src.baltor.graph.temporal.bridges — wire the temporal graph to the watchtower, reconciliation, and
consumption WITHOUT replacing any of them. The graph RECORDS freshness/conflict/serve decisions as nodes,
edges, and projections; the existing authorities still decide.
"""
from __future__ import annotations

from .contracts import VERIFIED_CURRENT, HELD_OUT, STALE, SUPERSEDED, NOT_SERVABLE, EPOCH
from .store import TemporalGraphStore
from .policy import project_current


# ── watchtower bridge ─────────────────────────────────────────────────────
def mark_stale(store: TemporalGraphStore, temporal_fact_id: str, *, now: str = EPOCH) -> None:
    """Watchtower says a fragile fact is stale → set state STALE (the prior verified state stays in the timeline)."""
    store.set_state(temporal_fact_id, STALE, now=now)


def refresh_observation(store: TemporalGraphStore, *, canonical_fact_key: str, tenant_id: str, scope: str,
                        subject: str, predicate: str, obj: str, value_normalized: str, source_authority: str,
                        source_handles: list, now: str, verify_receipt_id: str, unit: str = "",
                        source_version: str = "v2") -> dict:
    """A verification task refreshed the fact → append a NEW observation, write VERIFIED_BY, re-project.
    The old stale observation/node remains queryable in the timeline (lossless)."""
    n = store.add_observation(canonical_fact_key=canonical_fact_key, tenant_id=tenant_id, scope=scope,
                              subject=subject, predicate=predicate, obj=obj, value_normalized=value_normalized,
                              source_authority=source_authority, source_handles=source_handles, unit=unit,
                              now=now, claim_status="atomic_fact", source_version=source_version)
    n.verification_receipt_ids.append(verify_receipt_id)
    store.add_edge(tenant_id=tenant_id, from_id=n.temporal_fact_id, to_id=n.temporal_fact_id,
                   edge_type="VERIFIED_BY", edge_source="deterministic", receipt_id=verify_receipt_id, observed_at=now)
    state = project_current(store, canonical_fact_key=canonical_fact_key, tenant_id=tenant_id, now=now)
    return {"refreshed_node": n.to_dict(), "state": state, "timeline_len": len(store.timeline(canonical_fact_key, tenant_id))}


# ── reconciliation bridge ──────────────────────────────────────────────────
def record_reconciliation(store: TemporalGraphStore, *, winner_id: str, loser_id: str, tenant_id: str,
                          recon_receipt_id: str, now: str = EPOCH) -> list[dict]:
    """Record a reconciliation decision as graph edges (the reconciler decided; the graph records it).
    Loser is held out (preserved, queryable), not deleted."""
    edges = [
        store.add_edge(tenant_id=tenant_id, from_id=loser_id, to_id=winner_id, edge_type="CONTRADICTS",
                       edge_source="deterministic", receipt_id=recon_receipt_id, observed_at=now),
        store.add_edge(tenant_id=tenant_id, from_id=loser_id, to_id=winner_id, edge_type="HELD_OUT_BY",
                       edge_source="deterministic", receipt_id=recon_receipt_id, observed_at=now),
        store.add_edge(tenant_id=tenant_id, from_id=winner_id, to_id=loser_id, edge_type="RECONCILED_BY",
                       edge_source="deterministic", receipt_id=recon_receipt_id, observed_at=now),
    ]
    store.set_state(loser_id, HELD_OUT, now=now, reconciliation_receipt_ids=[recon_receipt_id])
    store.set_state(winner_id, VERIFIED_CURRENT, now=now, reconciliation_receipt_ids=[recon_receipt_id])
    return edges


# ── consumption bridge ─────────────────────────────────────────────────────
def select_current_for_consumption(store: TemporalGraphStore, *, tenant_id: str,
                                   fact_keys: list[str] | None = None) -> dict:
    """Select ONLY verified_current facts for serving; collect held_out as separate warnings; never serve
    held_out/superseded/stale/contested. Returns a consumption-ready slice with temporal metadata."""
    served, held = [], []
    for n in store.nodes(tenant_id):
        if fact_keys and n["canonical_fact_key"] not in fact_keys:
            continue
        if n["current_state"] == VERIFIED_CURRENT:
            served.append({"canonical_fact_key": n["canonical_fact_key"], "value": n["value_normalized"],
                           "unit": n["unit"], "source_handles": n["source_handles"],
                           "observed_at": n["last_observed_at"], "valid_from": n["valid_from"],
                           "current_state": n["current_state"], "verification_receipt_ids": n["verification_receipt_ids"]})
        elif n["current_state"] == HELD_OUT:
            held.append({"canonical_fact_key": n["canonical_fact_key"], "value": n["value_normalized"],
                         "source_authority": n["source_authority"], "reason": "held_out_by_reconciliation",
                         "source_handles": n["source_handles"]})
    return {"served_facts": served, "held_out_warnings": held,
            "excluded_states": sorted(NOT_SERVABLE), "tenant_id": tenant_id}
