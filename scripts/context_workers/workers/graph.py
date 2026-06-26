"""Graph extraction worker."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.graph.extract",
    lane="graph",
    description="Build claim, entity, and chunk graph edges.",
    emits=("nodes", "edges"),
    capabilities=("graph_extraction", "lineage_edges"),
    task_types=("graph.extract", "node_edge.build"),
    image="baltor-worker-cpu",
    output_contract="context_graph",
)
def graph_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = payload.get("chunks") or []
    entities = payload.get("entities") or []
    claims = payload.get("claims") or []
    nodes = list(entities)
    nodes.extend({"id": c["id"], "label": c["id"], "type": "chunk", "weight": c.get("char_count", 0)} for c in chunks)
    nodes.extend({"id": c["id"], "label": c.get("subject", "claim"), "type": "claim"} for c in claims)
    edges = list(payload.get("entity_edges") or [])
    entity_by_label = {e.get("label", ""): e.get("id") for e in entities}
    for claim in claims:
        edges.append({"from": claim["id"], "to": claim["source_chunk"], "type": "supported_by"})
        eid = entity_by_label.get(claim.get("subject", ""))
        if eid:
            edges.append({"from": claim["id"], "to": eid, "type": "mentions"})
    return TaskResult.success({"nodes": nodes, "edges": edges})
