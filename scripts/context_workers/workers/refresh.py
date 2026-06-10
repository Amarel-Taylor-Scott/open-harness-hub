"""Refresh planning and placeholder verification workers."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.priority import make_research_task
from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.refresh.plan",
    lane="refresh",
    description="Create search/tool refresh jobs for volatile or weakly supported facts.",
    emits=("refresh_jobs",),
    capabilities=("refresh_planning", "queue_policy"),
    task_types=("fact.refresh.plan",),
    image="baltor-worker-cpu",
    output_contract="refresh_jobs.v1",
)
def refresh_plan(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    updates = payload.get("updates") or []
    jobs = []
    for item in updates:
        jobs.append(make_research_task(run_id=ctx.run_id, tenant_id=ctx.tenant_id, fact=item))
    return TaskResult.success({"refresh_jobs": jobs})


@registry.register(
    "context.search.verify",
    lane="refresh",
    description="Placeholder search/tool verification worker; hosted deployments bind this to live search or governed tools.",
    emits=("verification_packet",),
    capabilities=("source_search", "verification_packet"),
    task_types=("verify.official_source.find", "verify.second_source.find"),
    image="baltor-worker-research",
    output_contract="verification_packet.v1",
)
def search_verify(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    query = str(payload.get("query") or "")
    fact_id = payload.get("fact_id")
    if not query:
        return TaskResult.failure("query required")
    return TaskResult.success({
        "verification_packet": {
            "fact_id": fact_id,
            "query": query,
            "status": "planned",
            "sources": [],
            "note": "No live search is executed by the local deterministic worker.",
        }
    })
