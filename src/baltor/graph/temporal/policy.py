"""src.baltor.graph.temporal.policy — the governed current-state projection.

Deterministically decides, per (canonical_fact_key, tenant, scope), which observed node is verified_current
and which are held_out / superseded / stale. Uses source authority (source-of-law beats FAQ) + freshness;
NEVER lets a newer lower-authority claim beat an older higher-authority one. This RECORDS the same decision
the existing reconciliation authority makes (assert-equivalence) — it does not replace reconciliation.
"""
from __future__ import annotations

from .contracts import VERIFIED_CURRENT, HELD_OUT, SUPERSEDED, STALE, CONTESTED, EPOCH
from .store import TemporalGraphStore


def _is_stale(node, now: str) -> bool:
    f = node.freshness or {}
    if f.get("no_refresh"):
        return False
    nva = f.get("next_verify_at")
    return bool(nva and now and now > nva)


def project_current(store: TemporalGraphStore, *, canonical_fact_key: str, tenant_id: str,
                    now: str = EPOCH, write_edges: bool = True) -> dict:
    """Project the governed current state for a fact_key. Sets node.current_state on every candidate and
    (optionally) writes CONTRADICTS edges between the winner and each held-out loser. Returns a
    TemporalFactState.v1 dict. Deterministic + reconstructable from observations + this policy."""
    cands = store.by_fact_key(canonical_fact_key, tenant_id)
    # tenant_override is a per-tenant lane and never changes the global winner; handle separately.
    globals_ = [n for n in cands if n.scope in ("global_public", "system_reference")]
    overrides = [n for n in cands if n.scope in ("tenant_private", "tenant_override")]

    winner = None
    if globals_:
        # highest authority first; ties broken by most-recent observation.
        ranked = sorted(globals_, key=lambda n: (n.authority_rank(), n.last_observed_at), reverse=True)
        top = ranked[0]
        if _is_stale(top, now):
            # the HIGHEST-authority fact is stale → no verified_current (queued for refresh). CRITICAL: do NOT
            # promote a lower-authority claim just because the authority went stale (FAQ-30 stays held out).
            top.current_state = STALE
            for n in ranked[1:]:
                if _is_stale(n, now):
                    n.current_state = STALE
                elif n.value_normalized != top.value_normalized:
                    n.current_state = HELD_OUT  # still held out vs the (stale) authority; never promoted
                else:
                    n.current_state = SUPERSEDED
            winner = None
        else:
            winner = top
            for n in globals_:
                if n.temporal_fact_id == winner.temporal_fact_id:
                    n.current_state = VERIFIED_CURRENT
                elif _is_stale(n, now):
                    n.current_state = STALE
                elif n.value_normalized != winner.value_normalized:
                    # lower-authority contradicting claim → held out (preserved, not deleted)
                    n.current_state = HELD_OUT
                    if write_edges:
                        store.add_edge(tenant_id=n.tenant_id, from_id=n.temporal_fact_id, to_id=winner.temporal_fact_id,
                                       edge_type="CONTRADICTS", edge_source="deterministic", policy_id="authority_then_freshness",
                                       policy_version="v1", observed_at=now)
                else:
                    # same value, lower authority, older → superseded by the winner
                    n.current_state = SUPERSEDED
                    if write_edges:
                        store.add_edge(tenant_id=n.tenant_id, from_id=winner.temporal_fact_id, to_id=n.temporal_fact_id,
                                       edge_type="SUPERSEDES", edge_source="deterministic", policy_id="authority_then_freshness",
                                       policy_version="v1", observed_at=now)
    for n in overrides:
        n.current_state = "tenant_override"

    held = [{"temporal_fact_id": n.temporal_fact_id, "value": n.value_normalized, "source_authority": n.source_authority,
             "reason": "lower_authority_conflict"} for n in globals_ if n.current_state == HELD_OUT]
    sup = [{"temporal_fact_id": n.temporal_fact_id, "value": n.value_normalized} for n in globals_ if n.current_state == SUPERSEDED]
    return {"schema_version": "TemporalFactState.v1", "canonical_fact_key": canonical_fact_key, "tenant_id": tenant_id,
            "scope": "global_public", "current_temporal_fact_id": winner.temporal_fact_id if winner else "",
            "current_value": winner.value_normalized if winner else "", "current_unit": winner.unit if winner else "",
            "current_state": winner.current_state if winner else (STALE if globals_ else "candidate"),
            "current_source_handles": list(winner.source_handles) if winner else [],
            "held_out": held, "superseded": sup, "as_of": now}
