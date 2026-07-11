"""Temporal adapter for Context Fidelity workflows.

Temporal is best for durable N-pass runs, human gates, long-running refreshes,
and workflows that must survive process or cluster failures. Activities call the
same registry used by local, Redis/KEDA, and Celery execution.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

try:
    from temporalio import activity, workflow
    from temporalio.common import RetryPolicy
except ImportError as exc:  # pragma: no cover - optional dependency
    raise SystemExit("Install optional dependency `temporalio` to use this backend.") from exc

with workflow.unsafe.imports_passed_through():
    from scripts.context_workers.registry import registry
    from scripts.context_workers.tasks import ensure_registered


@activity.defn
async def run_context_activity(envelope: dict[str, Any]) -> dict[str, Any]:
    ensure_registered()
    result = registry.run(envelope)
    if not result.ok:
        raise RuntimeError(result.error or "context worker failed")
    return {"ok": result.ok, "output": result.output, "warnings": result.warnings, "enqueue": result.enqueue}


@workflow.defn
class ContextFidelityWorkflow:
    """Durable N-pass orchestration over the registry task envelope."""

    @workflow.run
    async def run(self, envelope: dict[str, Any], max_passes: int = 3) -> dict[str, Any]:
        queue = [envelope]
        outputs: list[dict[str, Any]] = []
        while queue:
            job = queue.pop(0)
            pass_index = int(job.get("pass_index") or 1)
            if pass_index > max_passes:
                continue
            result = await workflow.execute_activity(
                run_context_activity,
                job,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            outputs.append({"task": job.get("task"), "pass_index": pass_index, "result": result})
            for child in result.get("enqueue", []):
                child.setdefault("run_id", job.get("run_id"))
                child.setdefault("tenant_id", job.get("tenant_id", "local"))
                child.setdefault("parent_job_id", job.get("job_id"))
                child.setdefault("pass_index", pass_index + 1)
                queue.append(child)
        return {"ok": True, "outputs": outputs}
