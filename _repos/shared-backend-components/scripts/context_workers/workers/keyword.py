"""Keyword analysis worker."""
from __future__ import annotations

from collections import Counter
from typing import Any

from scripts.context_workers.common import STOP_WORDS, WORD_RE
from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.keyword",
    lane="analyze",
    description="Extract high-signal keyword counts from chunks.",
    emits=("keywords",),
    capabilities=("keyword_analysis", "facet_counts"),
    task_types=("keyword.extract",),
    image="baltor-worker-cpu",
    output_contract="keywords",
)
def keyword_analysis(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    text = " ".join(c.get("text", "") for c in payload.get("chunks", [])) or str(payload.get("text") or "")
    counts = Counter(w.lower() for w in WORD_RE.findall(text) if w.lower() not in STOP_WORDS)
    keywords = [{"term": term, "count": count} for term, count in counts.most_common(40)]
    return TaskResult.success({"keywords": keywords})
