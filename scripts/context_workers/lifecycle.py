"""Standard lifecycle wrapper for Context Fidelity workers.

Worker functions stay small and deterministic; this module owns the operational
contract around them: preflight, payload loading, JSON logging, runtime metadata,
execution timing, follow-up counts, and closeout state.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

from scripts._config import CONTEXT_WORKER_RUNTIME_SETTINGS
from scripts.context_workers.registry import TaskContext, TaskResult, WorkerRegistry, WorkerSpec
from scripts.context_workers.runtime_io import HeartbeatStore, runtime_health
from scripts.db.runtime_settings import runtime_setting

LIFECYCLE_VERSION = "context-worker-lifecycle"
CONTEXT_WORKER_RUNTIME_NAMESPACE = "baltor.context_worker.runtime"


def _worker_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_WORKER_RUNTIME_NAMESPACE,
        definitions=CONTEXT_WORKER_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_RUNTIME_BACKEND = _worker_setting("backend")


@dataclass(frozen=True)
class WorkerRuntime:
    backend: str
    hostname: str
    pid: int
    queue_key: str
    ledger_path: str
    image: str
    lifecycle_version: str = LIFECYCLE_VERSION

    @classmethod
    def from_env(cls, *, queue_key: str = "", ledger_path: str = "", image: str = "") -> "WorkerRuntime":
        return cls(
            backend=_worker_setting("backend"),
            hostname=socket.gethostname(),
            pid=os.getpid(),
            queue_key=queue_key,
            ledger_path=ledger_path,
            image=image or _worker_setting("image"),
        )


class JsonLifecycleLogger:
    def __init__(self, *, enabled: bool | None = None) -> None:
        raw = _worker_setting("json_logs").lower()
        self.enabled = enabled if enabled is not None else raw not in {"0", "false", "no", "off"}

    def emit(
        self,
        event: str,
        *,
        job: dict[str, Any],
        runtime: WorkerRuntime,
        detail: dict[str, Any] | None = None,
        severity: str = "INFO",
    ) -> None:
        if not self.enabled:
            return
        line = {
            "ts": int(time.time()),
            "severity": severity,
            "event": event,
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "tenant_id": job.get("tenant_id"),
            "trace_id": job.get("trace_id") or job.get("run_id"),
            "span_id": job.get("job_id"),
            "runtime": asdict(runtime),
            "detail": detail or {},
        }
        print(json.dumps(line, sort_keys=True), file=sys.stderr, flush=True)


def preflight_task(job: dict[str, Any], spec: WorkerSpec) -> dict[str, Any]:
    payload = job.get("payload")
    runtime_probe = runtime_health()
    checks = [
        {"name": "job_id_present", "ok": bool(str(job.get("job_id") or "").strip())},
        {"name": "task_matches_worker", "ok": str(job.get("task") or job.get("kind") or "") == spec.name},
        {"name": "run_id_present", "ok": bool(str(job.get("run_id") or "").strip())},
        {"name": "tenant_id_present", "ok": bool(str(job.get("tenant_id") or "").strip())},
        {"name": "payload_is_object", "ok": isinstance(payload, dict)},
        {"name": "worker_has_output_contract", "ok": bool(spec.output_contract)},
        {"name": "runtime_paths_writable", "ok": bool(runtime_probe.get("ok")), "detail": runtime_probe},
    ]
    return {
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
        "worker": spec.name,
        "lane": spec.lane,
        "output_contract": spec.output_contract,
        "idempotent": spec.idempotent,
        "max_retries": spec.max_retries,
    }


def _context_from_job(job: dict[str, Any]) -> TaskContext:
    return TaskContext(
        job_id=str(job.get("job_id") or ""),
        run_id=str(job.get("run_id") or "local"),
        tenant_id=str(job.get("tenant_id") or "local"),
        pass_index=int(job.get("pass_index") or 1),
        parent_job_id=job.get("parent_job_id"),
    )


def execute_task_lifecycle(
    registry: WorkerRegistry,
    job: dict[str, Any],
    *,
    runtime: WorkerRuntime,
    logger: JsonLifecycleLogger | None = None,
    heartbeat: HeartbeatStore | None = None,
) -> tuple[TaskResult, dict[str, Any]]:
    logger = logger or JsonLifecycleLogger()
    heartbeat = heartbeat or HeartbeatStore()
    started = time.perf_counter()
    lifecycle: dict[str, Any] = {
        "version": LIFECYCLE_VERSION,
        "stages": [],
        "runtime": asdict(runtime),
    }

    def mark(stage: str, status: str, detail: dict[str, Any] | None = None) -> None:
        item = {"stage": stage, "status": status, "ts": int(time.time()), "detail": detail or {}}
        lifecycle["stages"].append(item)
        severity = "ERROR" if status == "failed" else "INFO"
        heartbeat.write(job=job, runtime=runtime, stage=stage, status=status, detail=detail)
        logger.emit(f"worker.{stage}.{status}", job=job, runtime=runtime, detail=detail, severity=severity)

    try:
        spec = registry.get(str(job.get("task") or job.get("kind") or ""))
    except Exception as exc:  # noqa: BLE001 - this is the preflight failure path
        mark("preflight", "failed", {"error": repr(exc)})
        lifecycle["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
        return TaskResult.failure("preflight_failed", output={"lifecycle": lifecycle}), lifecycle

    mark("preflight", "started", {"worker": spec.name})
    preflight = preflight_task(job, spec)
    mark("preflight", "complete" if preflight["ok"] else "failed", preflight)
    if not preflight["ok"]:
        lifecycle["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
        return TaskResult.failure("preflight_failed", output={"preflight": preflight, "lifecycle": lifecycle}), lifecycle

    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    mark("load", "complete", {"payload_keys": sorted(payload.keys())})
    mark("execute", "started", {"worker": spec.name, "lane": spec.lane})
    try:
        result = spec.handler(_context_from_job(job), payload)
    except Exception as exc:  # noqa: BLE001 - isolate poison jobs and preserve ledger shape
        lifecycle["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
        mark("execute", "failed", {"error": repr(exc)})
        mark("closeout", "complete", {"ok": False, "error": repr(exc)})
        return TaskResult.failure(repr(exc), output={"lifecycle": lifecycle}), lifecycle

    mark("execute", "complete", {"ok": result.ok, "output_keys": sorted(result.output.keys()), "warnings": len(result.warnings)})
    mark("emit_followups", "complete", {"child_job_count": len(result.enqueue)})
    lifecycle["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
    mark("closeout", "complete", {
        "ok": result.ok,
        "error": result.error,
        "duration_ms": lifecycle["duration_ms"],
        "child_job_count": len(result.enqueue),
    })
    return result, lifecycle
