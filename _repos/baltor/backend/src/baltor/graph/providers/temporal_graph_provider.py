"""src.baltor.graph.providers.temporal_graph_provider — the temporal_graph_provider capability seam.

Baltor's LOCAL temporal graph is the source of truth for serving. Graphiti is a CANDIDATE provider: it may
assist retrieval / propose edges, but its output is a provider PROJECTION, never canonical truth. A missing
Graphiti dependency is NOT a blocker — the deterministic emulator implements the same contract offline.

Providers: temporal_graph.baltor_local@v1 (active) · temporal_graph.graphiti@candidate (stub; UnavailableProvider
without the package) · temporal_graph.graphiti_emulator@v1 (deterministic offline emulator).
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..temporal.store import TemporalGraphStore


class UnavailableProvider(Exception):
    """A candidate provider has no working backend (e.g. Graphiti not installed). Never fabricate truth."""


@runtime_checkable
class TemporalGraphProviderPort(Protocol):
    provider_id: str

    def project(self, store: TemporalGraphStore, tenant_id: str) -> dict:  # read-only projection
        ...

    def status(self) -> dict:  # TemporalGraphProviderStatus
        ...


def _status(provider_id: str, status: str, available: bool, reason: str = "", credential_ref: str = "") -> dict:
    return {"schema_version": "TemporalGraphProviderStatus", "provider_id": provider_id, "status": status,
            "available": available, "reason": reason, "credential_ref": credential_ref}


def _projection(store: TemporalGraphStore, tenant_id: str, provider_id: str) -> dict:
    snap = store.snapshot(tenant_id)
    return {"schema_version": "TemporalGraphProjection", "tenant_id": tenant_id, "scope": "global_public",
            "provider_id": provider_id, "facts": snap["facts"], "edges": snap["edges"], "as_of": ""}


class BaltorLocalTemporalGraph:
    """The authoritative local provider — pure stdlib, no external deps."""
    provider_id = "temporal_graph.baltor_local@v1"

    def project(self, store: TemporalGraphStore, tenant_id: str) -> dict:
        return _projection(store, tenant_id, self.provider_id)

    def status(self) -> dict:
        return _status(self.provider_id, "active", True)


class GraphitiCandidate:
    """Graphiti wrapper — CANDIDATE. No SDK import; raises UnavailableProvider until a real backend lands."""
    provider_id = "temporal_graph.graphiti@candidate"

    def project(self, store: TemporalGraphStore, tenant_id: str) -> dict:
        raise UnavailableProvider("graphiti not installed; set GRAPHITI_URL + install the cataloged adapter (env://GRAPHITI_API_KEY)")

    def status(self) -> dict:
        return _status(self.provider_id, "candidate", False,
                       "graphiti package/client not installed (candidate; emulator covers the contract)",
                       "env://GRAPHITI_API_KEY")


class GraphitiEmulator:
    """Deterministic offline emulator implementing the SAME contract as the real Graphiti provider would —
    so the correctness invariant runs with NO external dependency. Projects the local store in a graphiti-ish shape."""
    provider_id = "temporal_graph.graphiti_emulator@v1"

    def project(self, store: TemporalGraphStore, tenant_id: str) -> dict:
        p = _projection(store, tenant_id, self.provider_id)
        # graphiti-ish view: nodes/edges renamed, but the SAME governed facts/edges (a projection, not truth).
        p["graphiti_view"] = {"episodes": [f["temporal_fact_id"] for f in p["facts"]],
                              "relations": [(e["from_temporal_fact_id"], e["edge_type"], e["to_temporal_fact_id"]) for e in p["edges"]]}
        return p

    def status(self) -> dict:
        return _status(self.provider_id, "emulated", True, "deterministic offline emulator (no graphiti dependency)")


PROVIDERS = {p.provider_id: p for p in (BaltorLocalTemporalGraph(), GraphitiCandidate(), GraphitiEmulator())}


def get_provider(provider_id: str) -> TemporalGraphProviderPort:
    if provider_id not in PROVIDERS:
        raise KeyError(f"unknown temporal_graph_provider {provider_id!r}")
    return PROVIDERS[provider_id]
