"""Entity extraction worker."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.common import chunk_text, entities, stable_hash
from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.entity.extract",
    lane="analyze",
    description="Extract candidate entities and chunk mentions.",
    emits=("entities", "edges"),
    capabilities=("entity_extraction", "local_rules"),
    task_types=("entity.extract",),
    image="baltor-worker-cpu",
    output_contract="entities",
)
def entity_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = payload.get("chunks") or chunk_text(str(payload.get("text") or ""))
    full_text = " ".join(c.get("text", "") for c in chunks)
    labels = entities(full_text)[:80]
    nodes = [{"id": stable_hash("entity", e, i + 1), "label": e, "type": "entity"} for i, e in enumerate(labels)]
    node_by_label = {n["label"]: n["id"] for n in nodes}
    edges = []
    for chunk in chunks:
        for entity in labels:
            if entity in chunk.get("text", ""):
                edges.append({"from": node_by_label[entity], "to": chunk["id"], "type": "mentioned_in"})
    return TaskResult.success({"entities": nodes, "entity_edges": edges})
