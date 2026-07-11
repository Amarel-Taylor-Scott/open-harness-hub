"""Queue runner for registered Context Fidelity workers."""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import uuid
import warnings
from pathlib import Path
from typing import Any

from scripts._config import CONTEXT_WORKER_RUNTIME_SETTINGS
from scripts.context_workers.lifecycle import JsonLifecycleLogger, WorkerRuntime, execute_task_lifecycle, preflight_task
from scripts.context_workers.registry import registry
from scripts.context_workers.router import route_task
from scripts.context_workers.runtime_io import ArtifactStore, HeartbeatStore, IdempotencyStore, runtime_health
from scripts.context_workers.tasks import ensure_registered
from scripts.db.runtime_settings import runtime_setting
from scripts.foundry.queues import from_env as queue_from_env
from scripts.model_gateway import resolve_model_route


CONTEXT_WORKER_RUNTIME_NAMESPACE = "baltor.context_worker.runtime"


def _worker_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_WORKER_RUNTIME_NAMESPACE,
        definitions=CONTEXT_WORKER_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_LEDGER = Path(_worker_setting("ledger_path"))
DEFAULT_CONTEXT_QUEUE_KEY = _worker_setting("context_queue_key")
DEFAULT_CONTEXT_EVENT_STREAM = _worker_setting("context_event_stream")
SCHEMAS_DIR = Path("schemas")
SHUTDOWN_REQUESTED = False


def _request_shutdown(signum: int, _frame: object) -> None:
    global SHUTDOWN_REQUESTED
    SHUTDOWN_REQUESTED = True
    print(json.dumps({
        "ts": int(time.time()),
        "event": "worker.shutdown.requested",
        "signal": signum,
    }, sort_keys=True), file=sys.stderr, flush=True)


def install_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)


def queue_key() -> str:
    return _worker_setting("context_queue_key")


def event_stream_key() -> str:
    return _worker_setting("context_event_stream")


def _publish_worker_event(event: str, *, job: dict[str, Any] | None = None, detail: dict[str, Any] | None = None) -> None:
    redis_url = _worker_setting("redis_url")
    if not redis_url:
        return
    try:
        import redis  # type: ignore

        client = redis.from_url(redis_url, decode_responses=True)
        payload = {
            "ts": int(time.time()),
            "event": event,
            "job_id": (job or {}).get("job_id", ""),
            "task": (job or {}).get("task", ""),
            "run_id": (job or {}).get("run_id", ""),
            "tenant_id": (job or {}).get("tenant_id", ""),
            "detail": detail or {},
        }
        client.xadd(event_stream_key(), {"event": json.dumps(payload, sort_keys=True)}, maxlen=1000, approximate=True)
    except Exception:
        return


def enqueue_task(queue: Any, *, task: str, payload: dict[str, Any], run_id: str | None = None,
                 tenant_id: str = "local", pass_index: int = 1) -> dict[str, Any]:
    job = {
        "job_id": f"cw-{uuid.uuid4().hex[:12]}",
        "task": task,
        "run_id": run_id or f"run-{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "pass_index": pass_index,
        "payload": payload,
        "queued_at": int(time.time()),
    }
    queue.enqueue(job)
    return job


def _runtime_for_job(job: dict[str, Any], *, ledger_path: Path) -> WorkerRuntime:
    image = "local-python"
    try:
        image = registry.get(str(job.get("task") or job.get("kind") or "")).image
    except Exception:
        pass
    return WorkerRuntime.from_env(queue_key=queue_key(), ledger_path=str(ledger_path), image=image)


def _write_ledger(record: dict[str, Any], ledger_path: Path) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def _close_record(record: dict[str, Any], *, ledger_path: Path, artifact_store: ArtifactStore, idempotency: IdempotencyStore, idempotency_key: str | None = None) -> dict[str, Any]:
    record["artifact_refs"] = artifact_store.write_job_artifacts(record)
    if idempotency_key:
        idempotency.close(idempotency_key, status="complete" if record.get("ok") else "failed", record=record)
    _write_ledger(record, ledger_path)
    return record


def _budget_policy(job: dict[str, Any]) -> dict[str, Any]:
    for candidate in (
        job.get("budget_policy"),
        (job.get("queue_policy") if isinstance(job.get("queue_policy"), dict) else {}).get("budget_policy"),
        (job.get("payload") if isinstance(job.get("payload"), dict) else {}).get("budget_policy"),
    ):
        if isinstance(candidate, dict):
            return candidate
    return {}


def _auto_approves_local_job(job: dict[str, Any], policy: dict[str, Any]) -> bool:
    if _worker_setting("local_auto_approve").lower() not in {"1", "true", "yes"}:
        return False
    if "frontier_or_human_review_requires_approval" in set(policy.get("reason_codes") or []):
        payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        model_route = payload.get("model_route") if isinstance(payload.get("model_route"), dict) else {}
        selected = model_route.get("selected_route") if isinstance(model_route.get("selected_route"), dict) else {}
        return selected.get("trust_boundary") == "local" and selected.get("data_retention") == "local"
    if "frontier_audit_requires_approval" in set(policy.get("reason_codes") or []):
        return str(job.get("task") or "").startswith("llm.")
    return False


def _budget_gate_record(job: dict[str, Any]) -> dict[str, Any] | None:
    policy = _budget_policy(job)
    action = str(policy.get("action") or "allow")
    approved = bool(job.get("budget_override_approved") or policy.get("approved"))
    if action == "require_approval" and _auto_approves_local_job(job, policy):
        policy["action"] = "allow"
        policy["auto_approved"] = True
        policy.setdefault("reason_codes", []).append("auto_approved_local_read_only")
        return None
    if action == "block":
        return {
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "ok": False,
            "error": "budget_blocked",
            "output": {"budget_policy": policy},
            "warnings": list(policy.get("reason_codes") or ["tenant_budget_blocked"]),
            "finished_at": int(time.time()),
        }
    if action == "require_approval" and not approved:
        return {
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "ok": False,
            "error": "approval_required",
            "output": {"budget_policy": policy},
            "warnings": list(policy.get("reason_codes") or ["budget_approval_required"]),
            "finished_at": int(time.time()),
        }
    return None


def _route_budget_gate_job(queue: Any, job: dict[str, Any], error: str) -> None:
    job["_hold_reason"] = error
    if error == "approval_required":
        if callable(getattr(queue, "hold_for_approval", None)):
            queue.hold_for_approval(job)
        elif callable(getattr(queue, "hold", None)):
            queue.hold(job)
        elif callable(getattr(queue, "dead_letter", None)):
            queue.dead_letter(job)
        else:
            queue.ack(job)
        return
    if error == "budget_blocked":
        if callable(getattr(queue, "block_for_budget", None)):
            queue.block_for_budget(job)
        elif callable(getattr(queue, "block", None)):
            queue.block(job)
        elif callable(getattr(queue, "dead_letter", None)):
            queue.dead_letter(job)
        else:
            queue.ack(job)
        return
    if callable(getattr(queue, "fail_permanently", None)):
        queue.fail_permanently(job)
    elif callable(getattr(queue, "dead_letter", None)):
        queue.dead_letter(job)
    else:
        queue.ack(job)


def process_one(queue: Any, *, ledger_path: Path = DEFAULT_LEDGER) -> dict[str, Any] | None:
    ensure_registered()
    job = queue.pull()
    if job is None:
        return None
    _publish_worker_event("worker.job.claimed", job=job, detail={"queue": queue_key()})
    runtime = _runtime_for_job(job, ledger_path=ledger_path)
    lifecycle_logger = JsonLifecycleLogger()
    artifact_store = ArtifactStore()
    idempotency = IdempotencyStore()
    heartbeat = HeartbeatStore()
    acquisition = idempotency.acquire(job, runtime=runtime)
    if not acquisition["acquired"]:
        existing = acquisition.get("existing") or {}
        duplicate_record = {
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "ok": True,
            "error": "",
            "output": {"duplicate_of": existing.get("job_id"), "idempotency": existing},
            "warnings": ["duplicate_idempotency_key"],
            "runtime": runtime.__dict__,
            "lifecycle": {
                "version": runtime.lifecycle_version,
                "runtime": runtime.__dict__,
                "stages": [
                    {"stage": "idempotency", "status": "duplicate", "ts": int(time.time()), "detail": acquisition},
                    {"stage": "closeout", "status": "complete", "ts": int(time.time()), "detail": {"ok": True, "duplicate": True}},
                ],
            },
            "finished_at": int(time.time()),
        }
        if callable(getattr(queue, "ack", None)):
            queue.ack(job)
        lifecycle_logger.emit("worker.idempotency.duplicate", job=job, runtime=runtime, detail=acquisition)
        _publish_worker_event("worker.idempotency.duplicate", job=job, detail=acquisition)
        return _close_record(duplicate_record, ledger_path=ledger_path, artifact_store=artifact_store, idempotency=idempotency)
    heartbeat.write(job=job, runtime=runtime, stage="claim", status="acquired", detail={"idempotency_key": acquisition["key"]})
    gate_record = _budget_gate_record(job)
    if gate_record is not None:
        _route_budget_gate_job(queue, job, str(gate_record["error"]))
        gate_record["runtime"] = runtime.__dict__
        gate_record["lifecycle"] = {
            "version": runtime.lifecycle_version,
            "runtime": runtime.__dict__,
            "stages": [
                {"stage": "preflight", "status": "complete", "ts": int(time.time()), "detail": {"budget_policy_checked": True}},
                {"stage": "budget_gate", "status": str(gate_record["error"]), "ts": int(time.time()), "detail": gate_record["output"]},
                {"stage": "closeout", "status": "complete", "ts": int(time.time()), "detail": {"ok": False}},
            ],
        }
        lifecycle_logger.emit("worker.budget_gate." + str(gate_record["error"]), job=job, runtime=runtime, detail=gate_record["output"])
        _publish_worker_event("worker.budget_gate." + str(gate_record["error"]), job=job, detail=gate_record["output"])
        return _close_record(gate_record, ledger_path=ledger_path, artifact_store=artifact_store, idempotency=idempotency, idempotency_key=acquisition["key"])
    try:
        result, lifecycle = execute_task_lifecycle(registry, job, runtime=runtime, logger=lifecycle_logger, heartbeat=heartbeat)
        record = {
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "ok": result.ok,
            "error": result.error,
            "output": result.output,
            "warnings": result.warnings,
            "runtime": runtime.__dict__,
            "lifecycle": lifecycle,
            "finished_at": int(time.time()),
        }
        for child in result.enqueue:
            child.setdefault("run_id", job.get("run_id"))
            child.setdefault("tenant_id", job.get("tenant_id", "local"))
            child.setdefault("parent_job_id", job.get("job_id"))
            child.setdefault("pass_index", int(job.get("pass_index") or 1) + 1)
            child.setdefault("job_id", f"cw-{uuid.uuid4().hex[:12]}")
            child.setdefault("queued_at", int(time.time()))
            queue.enqueue(child)
            _publish_worker_event("worker.child.enqueued", job=child, detail={"parent_job_id": job.get("job_id"), "parent_task": job.get("task")})
        if result.ok:
            queue.ack(job)
        else:
            job["_attempts"] = int(job.get("_attempts", 0)) + 1
            queue.nack(job)
        _publish_worker_event("worker.job.closed", job=job, detail={"ok": result.ok, "error": result.error, "warnings": len(result.warnings), "children": len(result.enqueue)})
        return _close_record(record, ledger_path=ledger_path, artifact_store=artifact_store, idempotency=idempotency, idempotency_key=acquisition["key"])
    except Exception as exc:  # noqa: BLE001 - workers should isolate poison jobs
        job["_attempts"] = int(job.get("_attempts", 0)) + 1
        if job["_attempts"] > 2 and callable(getattr(queue, "fail_permanently", None)):
            queue.fail_permanently(job)
        elif job["_attempts"] > 2 and callable(getattr(queue, "dead_letter", None)):
            queue.dead_letter(job)
        else:
            queue.nack(job)
        lifecycle_logger.emit("worker.runner.exception", job=job, runtime=runtime, detail={"error": repr(exc)})
        _publish_worker_event("worker.job.exception", job=job, detail={"error": repr(exc)})
        record = {
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "ok": False,
            "error": repr(exc),
            "runtime": runtime.__dict__,
            "lifecycle": {
                "version": runtime.lifecycle_version,
                "runtime": runtime.__dict__,
                "stages": [{"stage": "closeout", "status": "failed", "ts": int(time.time()), "detail": {"error": repr(exc)}}],
            },
            "finished_at": int(time.time()),
        }
        return _close_record(record, ledger_path=ledger_path, artifact_store=artifact_store, idempotency=idempotency, idempotency_key=acquisition["key"])


def drain(queue: Any, *, max_jobs: int | None = None, ledger_path: Path = DEFAULT_LEDGER) -> int:
    n = 0
    while max_jobs is None or n < max_jobs:
        record = process_one(queue, ledger_path=ledger_path)
        if record is None:
            break
        n += 1
    return n


def watch(queue: Any, *, max_jobs: int | None = None, ledger_path: Path = DEFAULT_LEDGER,
          idle_sleep_s: float = 2.0) -> int:
    processed = 0
    while not SHUTDOWN_REQUESTED and (max_jobs is None or processed < max_jobs):
        record = process_one(queue, ledger_path=ledger_path)
        if record is None:
            time.sleep(idle_sleep_s)
            continue
        processed += 1
    return processed


def _queue_stats(queue: Any) -> dict[str, Any]:
    if callable(getattr(queue, "stats", None)):
        return queue.stats()
    return {"pending": queue.depth() if callable(getattr(queue, "depth", None)) else None}


def _list_queue_state(queue: Any, status: str, *, limit: int = 50) -> list[dict[str, Any]]:
    if not callable(getattr(queue, "list_jobs", None)):
        return []
    jobs = queue.list_jobs(status, limit=limit)
    return [
        {
            "job_id": job.get("job_id"),
            "task": job.get("task"),
            "run_id": job.get("run_id"),
            "tenant_id": job.get("tenant_id"),
            "hold_reason": job.get("_hold_reason"),
            "queued_at": job.get("queued_at"),
            "budget_policy": _budget_policy(job),
        }
        for job in jobs
    ]


def _requeue_governed_job(queue: Any, *, job_id: str, from_status: str, updates: dict[str, Any]) -> dict[str, Any]:
    if not callable(getattr(queue, "requeue_job", None)):
        return {"ok": False, "error": "queue_does_not_support_requeue", "job_id": job_id, "from_status": from_status}
    job = queue.requeue_job(job_id, from_status=from_status, updates=updates)
    if job is None:
        return {"ok": False, "error": "job_not_found", "job_id": job_id, "from_status": from_status}
    return {"ok": True, "job_id": job_id, "from_status": from_status, "requeued": job}


def validate_worker_manifest(manifest: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Validate generated worker manifests against the portable JSON Schema.

    This keeps the local decorator registry honest before K8s, Temporal, Argo,
    Celery, or managed-job adapters consume the manifest.
    """
    try:
        import jsonschema  # type: ignore[import]
        from jsonschema import Draft202012Validator  # type: ignore[import]
    except Exception as exc:  # pragma: no cover - environment guard
        return {"ok": False, "error": f"jsonschema_unavailable: {exc}"}

    manifest = manifest if manifest is not None else registry.manifest()
    schema_path = SCHEMAS_DIR / "worker-manifest.schema.json"
    common_path = SCHEMAS_DIR / "_common.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    common = json.loads(common_path.read_text(encoding="utf-8"))
    base = SCHEMAS_DIR.resolve().as_uri() + "/"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        resolver = jsonschema.RefResolver(
            base_uri=base,
            referrer=schema,
            store={
                base + "worker-manifest.schema.json": schema,
                base + "_common.schema.json": common,
            },
        )
    validator = Draft202012Validator(schema, resolver=resolver)
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(manifest):
        for error in sorted(validator.iter_errors(item), key=lambda e: list(e.path)):
            errors.append({
                "index": index,
                "worker": item.get("name"),
                "path": list(error.path),
                "message": error.message,
            })
    return {
        "ok": not errors,
        "worker_count": len(manifest),
        "error_count": len(errors),
        "errors": errors,
    }


def _schema_validator(schema_name: str) -> Any:
    import jsonschema  # type: ignore[import]
    from jsonschema import Draft202012Validator  # type: ignore[import]

    schema_path = SCHEMAS_DIR / schema_name
    common_path = SCHEMAS_DIR / "_common.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    common = json.loads(common_path.read_text(encoding="utf-8"))
    base = SCHEMAS_DIR.resolve().as_uri() + "/"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        resolver = jsonschema.RefResolver(
            base_uri=base,
            referrer=schema,
            store={
                base + schema_name: schema,
                base + "_common.schema.json": common,
            },
        )
    return Draft202012Validator(schema, resolver=resolver)


def validate_research_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate queueable research/follow-up task envelopes."""
    try:
        validator = _schema_validator("research-task.schema.json")
    except Exception as exc:  # pragma: no cover - environment guard
        return {"ok": False, "error": f"jsonschema_unavailable: {exc}"}
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(tasks):
        for error in sorted(validator.iter_errors(item), key=lambda e: list(e.path)):
            errors.append({
                "index": index,
                "task_id": item.get("task_id"),
                "task_type": item.get("task_type"),
                "path": list(error.path),
                "message": error.message,
            })
    return {
        "ok": not errors,
        "task_count": len(tasks),
        "error_count": len(errors),
        "errors": errors,
    }


def _load_research_tasks(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tasks", "research_tasks", "followup_tasks"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("expected a JSON task array or an object with tasks/research_tasks/followup_tasks")


def preflight_job(task: dict[str, Any]) -> dict[str, Any]:
    ensure_registered()
    try:
        spec = registry.get(str(task.get("task") or task.get("kind") or ""))
    except Exception as exc:  # noqa: BLE001 - CLI should report structured failure
        return {"ok": False, "error": repr(exc), "checks": [{"name": "worker_registered", "ok": False}]}
    result = preflight_task(task, spec)
    result["runtime"] = WorkerRuntime.from_env(queue_key=queue_key(), ledger_path=str(DEFAULT_LEDGER), image=spec.image).__dict__
    return result


def worker_health(queue: Any | None = None) -> dict[str, Any]:
    queue_stats = _queue_stats(queue) if queue is not None else {}
    return {
        "ok": True,
        "runtime": runtime_health(),
        "queue_key": queue_key(),
        "queue": type(queue).__name__ if queue is not None else "",
        "queue_stats": queue_stats,
        "workers_registered": len(registry.manifest()),
        "lifecycle_version": WorkerRuntime.from_env().lifecycle_version,
        "recent_heartbeats": HeartbeatStore().list_recent(limit=10),
    }


def _self_test() -> int:
    import tempfile
    from scripts.foundry.queues import SqliteQueue

    sample = "As of 2024, vendors must screen annually. Vendors must not ship above 65 percent risk."
    with tempfile.TemporaryDirectory() as tmp:
        runtime_dir_env = str(CONTEXT_WORKER_RUNTIME_SETTINGS["runtime_dir"]["env"])
        artifact_dir_env = str(CONTEXT_WORKER_RUNTIME_SETTINGS["artifact_dir"]["env"])
        old_runtime_dir = os.environ.get(runtime_dir_env)
        old_artifact_dir = os.environ.get(artifact_dir_env)
        os.environ[runtime_dir_env] = str(Path(tmp) / "runtime")
        os.environ[artifact_dir_env] = str(Path(tmp) / "artifacts")
        q = SqliteQueue(str(Path(tmp) / "q.sqlite"), key="context-test")
        job = enqueue_task(q, task="context.pipeline.pass", payload={"text": sample}, run_id="test")
        assert q.depth() == 1, "job was not queued"
        n = drain(q, max_jobs=1, ledger_path=Path(tmp) / "ledger.jsonl")
        assert n == 1, "job was not processed"
        ledger_record = json.loads((Path(tmp) / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert ledger_record["lifecycle"]["version"] == "context-worker-lifecycle", "lifecycle metadata missing"
        assert ledger_record["runtime"]["queue_key"], "runtime metadata missing queue key"
        assert q.depth() >= 1, "refresh child jobs were not queued"
        assert preflight_job(job)["ok"], "preflight did not accept valid job"
        assert ledger_record["artifact_refs"]["manifest"], "artifact manifest was not written"
        blocked_q = SqliteQueue(str(Path(tmp) / "blocked.sqlite"), key="context-test")
        blocked = enqueue_task(
            blocked_q,
            task="context.search.verify",
            payload={
                "query": "blocked test",
                "budget_policy": {"action": "block", "reason_codes": ["tenant_budget_remaining_too_low"]},
            },
            run_id="budget-test",
        )
        record = process_one(blocked_q, ledger_path=Path(tmp) / "blocked-ledger.jsonl")
        assert record and record["error"] == "budget_blocked", "budget block was not enforced"
        assert blocked_q.stats()["budget_blocked"] == 1, "budget blocked job was not routed explicitly"
        approval_q = SqliteQueue(str(Path(tmp) / "approval.sqlite"), key="context-test")
        approval = enqueue_task(
            approval_q,
            task="context.search.verify",
            payload={
                "query": "approval test",
                "budget_policy": {"action": "require_approval", "reason_codes": ["task_estimate_exceeds_ceiling"]},
            },
            run_id="approval-test",
        )
        approval_record = process_one(approval_q, ledger_path=Path(tmp) / "approval-ledger.jsonl")
        assert approval_record and approval_record["error"] == "approval_required", "approval hold was not enforced"
        assert approval_q.stats()["approval_required"] == 1, "approval-required job was not routed explicitly"
        held_jobs = _list_queue_state(approval_q, "approval_required")
        assert held_jobs and held_jobs[0]["job_id"] == approval["job_id"], "approval-required job was not listable"
        requeued = _requeue_governed_job(
            approval_q,
            job_id=approval["job_id"],
            from_status="approval_required",
            updates={
                "budget_override_approved": True,
                "budget_policy": {"action": "allow", "approved": True, "reason_codes": ["approved_by_operator"]},
            },
        )
        assert requeued["ok"] and approval_q.stats()["pending"] == 1, "approval-required job was not requeued"
        rerun_record = process_one(approval_q, ledger_path=Path(tmp) / "approval-rerun-ledger.jsonl")
        assert rerun_record and rerun_record["error"] != "approval_required", "approved job was held again"
        assert not rerun_record.get("warnings"), "approved rerun should execute, not be treated as a duplicate"
        manifest_result = validate_worker_manifest()
        assert manifest_result["ok"], f"worker manifest failed schema validation: {manifest_result}"
        print(json.dumps({
            "ok": True,
            "job_id": job["job_id"],
            "queued_children": q.depth(),
            "budget_blocked": blocked["job_id"],
            "approval_required": approval["job_id"],
            "manifest_workers": manifest_result["worker_count"],
        }, indent=2))
        if old_runtime_dir is None:
            os.environ.pop(runtime_dir_env, None)
        else:
            os.environ[runtime_dir_env] = old_runtime_dir
        if old_artifact_dir is None:
            os.environ.pop(artifact_dir_env, None)
        else:
            os.environ[artifact_dir_env] = old_artifact_dir
    return 0


def main(argv: list[str] | None = None) -> int:
    ensure_registered()
    install_signal_handlers()
    parser = argparse.ArgumentParser(description="Context Fidelity worker queue runner.")
    parser.add_argument("--manifest", action="store_true", help="print registered worker specs")
    parser.add_argument("--validate-manifest", action="store_true", help="validate registered worker specs against schemas/worker-manifest.schema.json")
    parser.add_argument("--validate-research-tasks", metavar="PATH", help="validate research/follow-up task envelopes against schemas/research-task.schema.json")
    parser.add_argument("--route-task", metavar="PATH", help="print the routing decision for a JSON task envelope")
    parser.add_argument("--preflight-task", metavar="PATH", help="validate one JSON task envelope before enqueue/execution")
    parser.add_argument("--resolve-model-route", metavar="PATH", help="print the policy-compliant model route for a JSON task envelope")
    parser.add_argument("--requeue-scan", metavar="PATH", help="scan fact/source JSON records and print deduped follow-up tasks")
    parser.add_argument("--adversarial-fixtures", action="store_true", help="run adversarial routing and follow-up policy fixtures")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--enqueue-pass", metavar="PATH", help="enqueue context.pipeline.pass for a text file")
    parser.add_argument("--run-inline-pass", metavar="PATH", help="run context.pipeline.pass directly for a text file")
    parser.add_argument("--serve", action="store_true", help="drain the configured queue and exit")
    parser.add_argument("--watch", action="store_true", help="continuously poll the configured queue")
    parser.add_argument("--queue-stats", action="store_true", help="print explicit queue state counts")
    parser.add_argument("--health", action="store_true", help="print worker runtime health, queue stats, and recent heartbeats")
    parser.add_argument("--queue-list", choices=["pending", "approval_required", "budget_blocked", "failed_permanently"], help="list jobs in an explicit queue state")
    parser.add_argument("--approve-job", metavar="JOB_ID", help="approve and requeue a job from approval_required")
    parser.add_argument("--requeue-budget-blocked-job", metavar="JOB_ID", help="override budget block and requeue a budget_blocked job")
    parser.add_argument("--requeue-failed-job", metavar="JOB_ID", help="requeue a failed_permanently job after fixing the producer/worker")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--idle-sleep", type=float, default=2.0)
    args = parser.parse_args(argv)

    if args.manifest:
        print(json.dumps(registry.manifest(), indent=2))
        return 0
    if args.validate_manifest:
        result = validate_worker_manifest()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    if args.validate_research_tasks:
        result = validate_research_tasks(_load_research_tasks(Path(args.validate_research_tasks)))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    if args.route_task:
        task = json.loads(Path(args.route_task).read_text(encoding="utf-8"))
        print(json.dumps(route_task(task).asdict(), indent=2))
        return 0
    if args.preflight_task:
        task = json.loads(Path(args.preflight_task).read_text(encoding="utf-8"))
        result = preflight_job(task)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    if args.resolve_model_route:
        task = json.loads(Path(args.resolve_model_route).read_text(encoding="utf-8"))
        print(json.dumps(resolve_model_route(task), indent=2, sort_keys=True))
        return 0
    if args.requeue_scan:
        from scripts.context_workers.requeue import _load_records, scan_requeue

        facts, sources = _load_records(Path(args.requeue_scan))
        tasks = scan_requeue(facts, sources)
        validation = validate_research_tasks(tasks)
        print(json.dumps({"tasks": tasks, "task_count": len(tasks), "validation": validation}, indent=2, sort_keys=True))
        return 0 if validation.get("ok") else 1
    if args.adversarial_fixtures:
        from scripts.context_workers.adversarial_fixtures import run_fixtures

        print(json.dumps(run_fixtures(), indent=2))
        return 0
    if args.self_test:
        return _self_test()
    if args.queue_stats:
        queue = queue_from_env(queue_key())
        print(json.dumps({"queue": type(queue).__name__, "queue_key": queue_key(), "stats": _queue_stats(queue)}, indent=2, sort_keys=True))
        return 0
    if args.health:
        queue = queue_from_env(queue_key())
        result = worker_health(queue)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    if args.queue_list:
        queue = queue_from_env(queue_key())
        print(json.dumps({
            "queue": type(queue).__name__,
            "queue_key": queue_key(),
            "status": args.queue_list,
            "jobs": _list_queue_state(queue, args.queue_list, limit=args.limit),
        }, indent=2, sort_keys=True))
        return 0
    if args.approve_job:
        queue = queue_from_env(queue_key())
        print(json.dumps(_requeue_governed_job(
            queue,
            job_id=args.approve_job,
            from_status="approval_required",
            updates={
                "budget_override_approved": True,
                "budget_policy": {"action": "allow", "approved": True, "reason_codes": ["approved_by_operator"]},
            },
        ), indent=2, sort_keys=True))
        return 0
    if args.requeue_budget_blocked_job:
        queue = queue_from_env(queue_key())
        print(json.dumps(_requeue_governed_job(
            queue,
            job_id=args.requeue_budget_blocked_job,
            from_status="budget_blocked",
            updates={
                "budget_override_approved": True,
                "budget_policy": {"action": "allow", "approved": True, "reason_codes": ["budget_override_by_operator"]},
            },
        ), indent=2, sort_keys=True))
        return 0
    if args.requeue_failed_job:
        queue = queue_from_env(queue_key())
        print(json.dumps(_requeue_governed_job(
            queue,
            job_id=args.requeue_failed_job,
            from_status="failed_permanently",
            updates={"requeued_after_failure_review": True},
        ), indent=2, sort_keys=True))
        return 0
    if args.enqueue_pass:
        queue = queue_from_env(queue_key())
        text = Path(args.enqueue_pass).read_text(encoding="utf-8")
        job = enqueue_task(queue, task="context.pipeline.pass", payload={"text": text})
        print(json.dumps({"enqueued": job, "queue": type(queue).__name__}, indent=2))
        return 0
    if args.run_inline_pass:
        text = Path(args.run_inline_pass).read_text(encoding="utf-8")
        result = registry.run({
            "job_id": f"cw-{uuid.uuid4().hex[:12]}",
            "task": "context.pipeline.pass",
            "run_id": f"run-{uuid.uuid4().hex[:12]}",
            "tenant_id": "local",
            "pass_index": 1,
            "payload": {"text": text},
        })
        print(json.dumps({"ok": result.ok, "output": result.output, "warnings": result.warnings, "children": result.enqueue}, indent=2))
        return 0 if result.ok else 1
    if args.serve:
        queue = queue_from_env(queue_key())
        print(json.dumps({"processed": drain(queue, max_jobs=args.max_jobs), "queue": type(queue).__name__}, indent=2))
        return 0
    if args.watch:
        queue = queue_from_env(queue_key())
        print(json.dumps({"watching": True, "queue": type(queue).__name__, "queue_key": queue_key()}))
        watch(queue, max_jobs=args.max_jobs, idle_sleep_s=args.idle_sleep)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
