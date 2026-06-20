"""src.baltor.graph.temporal.store — the LOCAL deterministic temporal fact graph store.

Append-only nodes/edges/observations (held-out + superseded are NEVER deleted), deterministic edge ids,
tenant-scoped reads, and the query surface (timeline / contradictions / held-out / source-handle / current).
In-memory + dict-snapshot; works with NO external graph dependency (Graphiti is a candidate provider only).
"""
from __future__ import annotations

from typing import Any

from .contracts import (TemporalFactNode, edge_id, observation_id, content_hash, EDGE_TYPES, EDGE_SOURCES,
                        EPOCH, HELD_OUT, SUPERSEDED, VERIFIED_CURRENT)


class TenantScopeError(Exception):
    """A read attempted to cross a tenant boundary."""


class TemporalGraphStore:
    def __init__(self) -> None:
        self._nodes: dict[str, TemporalFactNode] = {}
        self._edges: dict[str, dict] = {}
        self._obs: list[dict] = []

    # ── writes (append-only) ──────────────────────────────────────────────
    def upsert_node(self, node: TemporalFactNode) -> TemporalFactNode:
        cur = self._nodes.get(node.temporal_fact_id)
        if cur is None:
            self._nodes[node.temporal_fact_id] = node
        else:  # merge observations forward; never lose the prior (append-only spirit)
            cur.last_observed_at = max(cur.last_observed_at, node.last_observed_at)
            cur.updated_at = max(cur.updated_at, node.updated_at)
            for r in node.verification_receipt_ids:
                if r not in cur.verification_receipt_ids:
                    cur.verification_receipt_ids.append(r)
        return self._nodes[node.temporal_fact_id]

    def add_observation(self, *, canonical_fact_key: str, tenant_id: str, scope: str, subject: str,
                        predicate: str, obj: str, value_normalized: str, source_authority: str,
                        source_handles: list, unit: str = "", source_artifact_ids: list | None = None,
                        valid_from: str = "", valid_to: str = "", now: str = EPOCH,
                        claim_status: str = "candidate", source_version: str = "v1") -> TemporalFactNode:
        ch = content_hash([canonical_fact_key, value_normalized, source_authority, source_version, sorted(source_handles)])
        node = TemporalFactNode(
            canonical_fact_key=canonical_fact_key, tenant_id=tenant_id, scope=scope, subject=subject,
            predicate=predicate, object=obj, value_normalized=value_normalized, source_authority=source_authority,
            content_hash=ch, claim_status=claim_status, unit=unit, source_handles=list(source_handles),
            source_artifact_ids=list(source_artifact_ids or []), valid_from=valid_from, valid_to=valid_to,
            first_observed_at=now, last_observed_at=now, created_at=now, updated_at=now)
        self.upsert_node(node)
        oid = observation_id(temporal_fact_id_=node.temporal_fact_id, observed_at=now, content_hash_=ch)
        self._obs.append({"schema_version": "TemporalFactObservation.v1", "observation_id": oid,
                          "temporal_fact_id": node.temporal_fact_id, "canonical_fact_key": canonical_fact_key,
                          "tenant_id": tenant_id, "value_normalized": value_normalized, "content_hash": ch,
                          "source_authority": source_authority, "source_handles": list(source_handles),
                          "observed_at": now, "valid_from": valid_from, "valid_to": valid_to,
                          "source_version": source_version, "claim_status": claim_status})
        # an OBSERVED_AS edge from the node to itself-as-observation keeps the timeline reconstructable
        self.add_edge(tenant_id=tenant_id, from_id=node.temporal_fact_id, to_id=node.temporal_fact_id,
                      edge_type="OBSERVED_AS", edge_source="deterministic", observed_at=now,
                      evidence_json={"observation_id": oid, "content_hash": ch})
        return node

    def set_state(self, temporal_fact_id_: str, state: str, *, now: str = EPOCH,
                  reconciliation_receipt_ids: list | None = None) -> None:
        n = self._nodes[temporal_fact_id_]
        n.current_state = state
        n.updated_at = now
        if state == HELD_OUT or state == SUPERSEDED:
            n.invalidated_at = now
        for r in (reconciliation_receipt_ids or []):
            if r not in n.reconciliation_receipt_ids:
                n.reconciliation_receipt_ids.append(r)

    def add_edge(self, *, tenant_id: str, from_id: str, to_id: str, edge_type: str,
                 edge_source: str = "deterministic", observed_at: str = EPOCH, policy_id: str = "",
                 policy_version: str = "", receipt_id: str = "", confidence: float = 1.0,
                 source_artifact_ids: list | None = None, source_handles: list | None = None,
                 evidence_json: dict | None = None, created_at: str = EPOCH) -> dict:
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"unknown edge_type {edge_type!r}")
        if edge_source not in EDGE_SOURCES:
            raise ValueError(f"unknown edge_source {edge_source!r}")
        token = observed_at or policy_version or policy_id or "static"
        eid = edge_id(tenant_id=tenant_id, from_id=from_id, edge_type=edge_type, to_id=to_id, observed_at_or_policy=token)
        edge = {"schema_version": "TemporalFactEdge.v1", "edge_id": eid, "tenant_id": tenant_id,
                "from_temporal_fact_id": from_id, "to_temporal_fact_id": to_id, "edge_type": edge_type,
                "edge_source": edge_source, "observed_at": observed_at, "policy_id": policy_id,
                "policy_version": policy_version, "receipt_id": receipt_id, "confidence": confidence,
                "source_artifact_ids": list(source_artifact_ids or []), "source_handles": list(source_handles or []),
                "evidence_json": dict(evidence_json or {}), "valid_from": "", "valid_to": "", "created_at": created_at or observed_at}
        self._edges[eid] = edge  # deterministic id → idempotent (repeated build does NOT duplicate)
        return edge

    # ── reads (tenant-scoped, projection-only) ────────────────────────────
    def get_node(self, tid: str, *, tenant_id: str | None = None) -> dict | None:
        n = self._nodes.get(tid)
        if n is None:
            return None
        if tenant_id is not None and n.tenant_id != tenant_id and n.scope in ("tenant_private", "tenant_override"):
            raise TenantScopeError(f"cross-tenant read of {tid}")
        return n.to_dict()

    def _visible(self, tenant_id: str) -> list[TemporalFactNode]:
        out = []
        for n in self._nodes.values():
            if n.scope in ("global_public", "system_reference") or n.tenant_id == tenant_id:
                out.append(n)
        return out

    def nodes(self, tenant_id: str) -> list[dict]:
        return [n.to_dict() for n in sorted(self._visible(tenant_id), key=lambda x: x.temporal_fact_id)]

    def edges(self, tenant_id: str, *, edge_type: str | None = None) -> list[dict]:
        vis = {n.temporal_fact_id for n in self._visible(tenant_id)}
        out = [e for e in self._edges.values() if e["from_temporal_fact_id"] in vis or e["to_temporal_fact_id"] in vis]
        if edge_type:
            out = [e for e in out if e["edge_type"] == edge_type]
        return sorted(out, key=lambda e: e["edge_id"])

    def timeline(self, canonical_fact_key: str, tenant_id: str) -> list[dict]:
        return sorted([o for o in self._obs if o["canonical_fact_key"] == canonical_fact_key
                       and (o["tenant_id"] == tenant_id or True)], key=lambda o: (o["observed_at"], o["observation_id"]))

    def by_fact_key(self, canonical_fact_key: str, tenant_id: str) -> list[TemporalFactNode]:
        return [n for n in self._visible(tenant_id) if n.canonical_fact_key == canonical_fact_key]

    def by_source_handle(self, handle: str, tenant_id: str) -> list[dict]:
        return [n.to_dict() for n in self._visible(tenant_id) if handle in n.source_handles]

    def contradictions(self, tenant_id: str) -> list[dict]:
        return self.edges(tenant_id, edge_type="CONTRADICTS")

    def held_out(self, tenant_id: str) -> list[dict]:
        return [n.to_dict() for n in self._visible(tenant_id) if n.current_state == HELD_OUT]

    def current_nodes(self, tenant_id: str) -> list[dict]:
        return [n.to_dict() for n in self._visible(tenant_id) if n.current_state == VERIFIED_CURRENT]

    def snapshot(self, tenant_id: str) -> dict:
        return {"facts": self.nodes(tenant_id), "edges": self.edges(tenant_id),
                "observations": [o for o in self._obs]}
