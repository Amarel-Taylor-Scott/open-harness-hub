"""Claim extraction worker."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.common import (
    CLAIM_SIGNAL_RE,
    DATE_OR_NUMBER_RE,
    NEGATIVE_RE,
    POSITIVE_RE,
    chunk_text,
    entities,
    sentences,
    stable_hash,
    subject,
)
from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.claim.extract",
    lane="analyze",
    description="Extract candidate claims/facts from chunks.",
    emits=("claims",),
    capabilities=("claim_extraction", "fact_signals"),
    task_types=("claim.extract", "fact.candidate.detect"),
    image="baltor-worker-cpu",
    output_contract="claims.v1",
)
def claim_extract(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = payload.get("chunks") or chunk_text(str(payload.get("text") or ""))
    claims = []
    for chunk in chunks:
        chunk_entities = entities(chunk.get("text", ""))
        for sentence in sentences(chunk.get("text", "")):
            if not (CLAIM_SIGNAL_RE.search(sentence) or DATE_OR_NUMBER_RE.search(sentence)):
                continue
            polarity = "negative" if NEGATIVE_RE.search(sentence) else "positive" if POSITIVE_RE.search(sentence) else "neutral"
            n = len(claims) + 1
            claims.append({
                "id": stable_hash("claim", sentence, n),
                "claim": sentence,
                "subject": subject(sentence, chunk_entities),
                "source_chunk": chunk["id"],
                "polarity": polarity,
            })
    return TaskResult.success({"claims": claims, "claim_count": len(claims)})
