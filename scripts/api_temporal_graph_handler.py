"""scripts.api_temporal_graph_handler — PURE projection handler for the governed Temporal Fact Graph.

Read-only projections over the LOCAL temporal graph (built from the CFPB reference demo); never serves a
held-out/stale fact as current, never publishes truth, never crosses a tenant boundary, no secrets. The
rebuild route re-runs the deterministic builder (a runtime service), it does not mutate served truth.
Model: scripts/api_pipeline_handler.py / scripts/api_memory_handler.py.
"""
from __future__ import annotations

from src.baltor.graph.temporal import build_cfpb_temporal_graph
from src.baltor.graph.temporal.bridges import select_current_for_consumption
from src.baltor.graph.providers import BaltorLocalTemporalGraph, GraphitiCandidate, GraphitiEmulator

ROUTES = (
    "/api/graph/temporal/facts", "/api/graph/temporal/timeline", "/api/graph/temporal/current",
    "/api/graph/temporal/conflicts", "/api/graph/temporal/held-out", "/api/graph/temporal/edges",
    "/api/graph/temporal/provider-status", "/api/graph/temporal/rebuild", "/api/graph/temporal/query",
)


def owns(path: str) -> bool:
    p = path.rstrip("/")
    return any(p == r or p.startswith(r + "/") for r in ROUTES)


def _demo(tenant: str = "global"):
    return build_cfpb_temporal_graph(tenant_id=tenant)


def _tenant(query: dict | None) -> str:
    return (query or {}).get("tenant") or (query or {}).get("tenant_id") or "global"


def handle(method: str, path: str, query: dict | None = None) -> tuple:
    p = path.rstrip("/")
    tenant = _tenant(query)
    r = _demo(tenant)
    store = r["store"]
    if method == "POST" and p == "/api/graph/temporal/rebuild":
        return 200, {"schema_version": "TemporalGraphReceipt", "rebuilt": True, "projection_only": True,
                     "receipt": r["receipt"], "current": r["state"]["current_value"]}
    if method != "GET":
        return 405, {"error": "method not allowed", "path": path}
    if p == "/api/graph/temporal/facts":
        return 200, {"available": True, "tenant_id": tenant, "facts": store.nodes(tenant), "total": len(store.nodes(tenant)), "projection_only": True}
    if p == "/api/graph/temporal/edges":
        return 200, {"available": True, "tenant_id": tenant, "edges": store.edges(tenant), "projection_only": True}
    if p == "/api/graph/temporal/conflicts":
        return 200, {"available": True, "tenant_id": tenant, "conflicts": store.contradictions(tenant), "projection_only": True}
    if p == "/api/graph/temporal/held-out":
        return 200, {"available": True, "tenant_id": tenant, "held_out": store.held_out(tenant), "projection_only": True}
    if p == "/api/graph/temporal/provider-status":
        return 200, {"available": True, "providers": [BaltorLocalTemporalGraph().status(), GraphitiCandidate().status(), GraphitiEmulator().status()]}
    if p.startswith("/api/graph/temporal/timeline/"):
        key = p[len("/api/graph/temporal/timeline/"):]
        return 200, {"available": True, "tenant_id": tenant, "canonical_fact_key": key, "observations": store.timeline(key, tenant), "projection_only": True}
    if p.startswith("/api/graph/temporal/current/"):
        key = p[len("/api/graph/temporal/current/"):]
        sel = select_current_for_consumption(store, tenant_id=tenant, fact_keys=[key])
        return 200, {"available": True, "tenant_id": tenant, "canonical_fact_key": key,
                     "served_facts": sel["served_facts"], "held_out_warnings": sel["held_out_warnings"], "projection_only": True}
    if p == "/api/graph/temporal/current" or p == "/api/graph/temporal/query":
        sel = select_current_for_consumption(store, tenant_id=tenant)
        return 200, {"available": True, "tenant_id": tenant, "served_facts": sel["served_facts"],
                     "held_out_warnings": sel["held_out_warnings"], "projection_only": True}
    return 404, {"error": "unknown temporal-graph route", "path": path}
