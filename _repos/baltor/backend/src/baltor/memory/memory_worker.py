"""src.baltor.memory.memory_worker — C-MEM-2 DELTA: memory operations as DURABLE CAPABILITY TASKS.

A stateless executor that drains `memory.*` tasks from the DurableFleetLedger (the same atomic-claim
durable path the live supervisor dispatches), performing memory.write / memory.recall via the existing
BaltorLocalMemoryProvider and writing a MemoryTrace per op. It NEVER emits a CanonicalFact or a
ContextResponse — memory is candidate context only. Ownership is only via atomic claim; idempotent on the
durable ledger; safe-fails invalid commands. No second worker framework — reuses DurableFleetLedger.
"""
from __future__ import annotations

import json

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider
from src.baltor.memory import builder_memory

MEMORY_OPS = ("memory.write", "memory.recall", "memory.profile", "memory.capture_builder_state",
              "memory.provider_health")


def _trace(op: str, provider_id: str, now: str, produced: list) -> dict:
    return {"schema_version": "MemoryTrace", "trace_id": "tr-" + (produced[0] if produced else op)[:16],
            "tenant_id": "", "container": "memory", "operation": op, "provider_id": provider_id,
            "request_handle": op, "produced_artifact_ids": produced, "held_out_artifact_ids": [],
            "rejected_artifact_ids": [], "rollback_target": "", "occurred_at": now}


def process_memory_task(provider, task: dict) -> dict:
    """Execute ONE claimed memory task from its payload. Returns {op, result, trace, error?}. Never returns
    a CanonicalFact or ContextResponse — only MemoryArtifacts / MemorySearchResults / MemoryTraces."""
    op = task["capability_id"]
    payload = json.loads(task.get("payload_json") or "{}")
    req = dict(payload.get("request") or {})
    req.setdefault("tenant_id", task.get("tenant_id") or "baltor")
    req.setdefault("project", payload.get("project") or "baltor-build")
    req.setdefault("now", payload.get("now") or 0)
    if op == "memory.write":
        if not str(req.get("content") or "").strip():
            return {"op": op, "error": "memory.write requires non-empty content", "trace": None, "result": {}}
        # redact secrets before any write (memory must never store secrets)
        req["content"], _ = builder_memory.redact(req.get("content", ""))
        art = provider.write(req)
        return {"op": op, "result": {"artifact_id": art["artifact_id"], "claim_status": art.get("claim_status")},
                "trace": _trace(op, art["provider_id"], req["now"], [art["artifact_id"]]), "is_truth": False}
    if op in ("memory.recall", "memory.profile"):
        res = provider.search(req) if op == "memory.recall" else provider.profile(req)
        arts = res.get("results", res.get("artifacts", []))
        return {"op": op, "result": {"count": len(arts), "memory_artifact_ids": [a["artifact_id"] for a in arts],
                                     "is_truth": False, "claim_status": "candidate_context"},
                "trace": _trace(op, provider.status().get("provider_id", "memory.baltor_local@v1"), req["now"],
                                [a["artifact_id"] for a in arts]), "is_truth": False}
    if op == "memory.provider_health":
        return {"op": op, "result": provider.status(), "trace": _trace(op, "memory.baltor_local@v1", req["now"], [])}
    if op == "memory.capture_builder_state":
        cap = builder_memory.capture_builder_state(provider, now=int(req["now"]), **(payload.get("state") or {}))
        return {"op": op, "result": {"artifact_id": cap["artifact"]["artifact_id"]}, "trace": cap["trace"], "is_truth": False}
    return {"op": op, "error": f"unknown memory op {op!r}", "trace": None}


def run_memory_worker_durable(db: str, *, worker_id: str, capability: str = "memory.write",
                              provider=None, max_tasks: int = 1000) -> dict:
    """Drain `capability` memory tasks from the durable ledger via atomic claim → process → ack.
    Invalid payloads nack (safe-fail). Returns processed/written/failed counts."""
    from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
    provider = provider or BaltorLocalMemoryProvider()
    L = DurableFleetLedger(db)
    L.register_worker(worker_id=worker_id, capability_ids=[capability])
    L.set_worker_status(worker_id, "warm")
    processed = written = failed = 0
    while processed + failed < max_tasks:
        t = L.claim_task(worker_id=worker_id, capability_id=capability)
        if t is None:
            break
        L.start_task(t["task_id"], worker_id)
        try:
            out = process_memory_task(provider, t)
        except Exception as e:  # invalid payload / provider error → safe-fail (nack), never crash the worker
            out = {"op": t["capability_id"], "error": f"{type(e).__name__}: {e}", "trace": None, "result": {}}
        if out.get("error"):
            L.nack_task(t["task_id"], worker_id, {"failure_type": "schema_validation_failed", "error": out["error"]},
                        retryable=False)
            failed += 1
        else:
            L.ack_task(t["task_id"], worker_id, out["result"].get("memory_artifact_ids")
                       or ([out["result"]["artifact_id"]] if "artifact_id" in out["result"] else []))
            processed += 1
            if out["op"] in ("memory.write", "memory.capture_builder_state"):
                written += 1
    L.set_worker_status(worker_id, "stopped")
    L.close()
    return {"worker_id": worker_id, "processed": processed, "written": written, "failed": failed, "status": "stopped"}


__all__ = ["process_memory_task", "run_memory_worker_durable", "MEMORY_OPS"]
