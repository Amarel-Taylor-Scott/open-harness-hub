"""Chunking worker."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.common import chunk_text
from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.chunk",
    lane="normalize",
    description="Split raw context into stable chunk ids.",
    emits=("chunks",),
    capabilities=("text_chunking", "stable_ids"),
    task_types=("document.chunk",),
    image="baltor-worker-cpu",
    output_contract="chunks",
)
def chunk_context(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    text = str(payload.get("text") or "")
    if not text.strip():
        return TaskResult.failure("text required")
    target_chars = int(payload.get("target_chars") or 900)
    chunks = chunk_text(text, target_chars=target_chars)
    return TaskResult.success({"chunks": chunks, "chunk_count": len(chunks)})
