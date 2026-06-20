"""Celery adapter for the Context Fidelity worker registry.

Install `celery[redis]` only when this backend is selected. The task envelope
and registry remain the product contract.
"""
from __future__ import annotations
from typing import Any

try:
    from celery import Celery
except ImportError as exc:  # pragma: no cover - optional dependency
    raise SystemExit("Install optional dependency `celery[redis]` to use this backend.") from exc

from scripts._config import CONTEXT_WORKER_RUNTIME_SETTINGS
from scripts.context_workers.registry import registry
from scripts.context_workers.tasks import ensure_registered
from scripts.db.runtime_settings import runtime_setting


CONTEXT_WORKER_RUNTIME_NAMESPACE = "baltor.context_worker.runtime"


def _worker_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_WORKER_RUNTIME_NAMESPACE,
        definitions=CONTEXT_WORKER_RUNTIME_SETTINGS,
        name=name,
    )


BROKER_URL = _worker_setting("celery_broker_url")
RESULT_BACKEND = _worker_setting("celery_result_backend") or BROKER_URL

app = Celery("ohh_context_workers", broker=BROKER_URL, backend=RESULT_BACKEND)
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_default_queue=_worker_setting("celery_default_queue"),
)


@app.task(name="ohh.context.run_task", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def run_task(self, envelope: dict[str, Any]) -> dict[str, Any]:
    ensure_registered()
    result = registry.run(envelope)
    if not result.ok:
        raise RuntimeError(result.error or "context worker failed")
    for child in result.enqueue:
        child.setdefault("run_id", envelope.get("run_id"))
        child.setdefault("tenant_id", envelope.get("tenant_id", "local"))
        child.setdefault("parent_job_id", envelope.get("job_id"))
        child.setdefault("pass_index", int(envelope.get("pass_index") or 1) + 1)
        run_task.delay(child)
    return {"ok": result.ok, "output": result.output, "warnings": result.warnings, "children": len(result.enqueue)}
