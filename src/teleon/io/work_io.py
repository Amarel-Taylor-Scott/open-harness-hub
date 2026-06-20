"""src.teleon.io.work_io — pure projectors from a durable-runtime task record to the typed work-I/O contracts.

The work item itself IS the CapabilityTask.v1 record the FleetLedger already produces; these helpers name the
lifecycle projections (claim / ack-nack / dead-letter / idempotency) so every product reads the same shapes.
Pure + deterministic; no src.baltor import (inputs are plain dicts).
"""
from __future__ import annotations

#: the command/work core fields every work item (CapabilityTask record) must carry
WORK_ITEM_CORE_FIELDS = ("task_id", "tenant_id", "capability_id", "status", "idempotency_key", "attempt",
                         "max_attempts", "queue_name", "payload_ref", "created_at")

_TERMINAL_FAIL = "dead"


def project_work_item(task: dict) -> dict:
    """Identity projection of the work item (the CapabilityTask record). Validated against WORK_ITEM_CORE_FIELDS."""
    return dict(task)


def project_worker_claim(task: dict) -> dict:
    """WorkerClaim.v1 — who holds the lease, until when, at what attempt (after an atomic claim)."""
    return {"schema_version": "WorkerClaim.v1", "task_id": task["task_id"], "worker_id": task["lease_owner"],
            "lease_until": task["lease_until"], "claimed_at": task["claimed_at"], "status": task["status"],
            "attempt": task["attempt"]}


def project_ack_nack_receipt(task: dict, *, outcome: str, worker_id: str, retryable: bool | None = None) -> dict:
    """AckNackReceipt.v1 — the completion/failure outcome. worker_id is passed explicitly (the acting worker): a
    retryable nack requeues and CLEARS the lease, so the worker can't be recovered from the final task state.
    resulting_status reflects the task's end state (succeeded / queued=requeued / dead)."""
    return {"schema_version": "AckNackReceipt.v1", "task_id": task["task_id"], "worker_id": worker_id,
            "outcome": outcome, "resulting_status": task["status"], "retryable": retryable,
            "attempt": task["attempt"], "result_artifact_ids": list(task.get("result_artifact_ids", [])),
            "error_json": dict(task.get("error_json", {})),
            "finished_at": task.get("finished_at") or None, "failed_at": task.get("failed_at") or None}


def project_dead_letter(task: dict) -> dict:
    """DeadLetterEntry.v1 — a terminally-failed work item, preserved with its last error for inspect/replay."""
    return {"schema_version": "DeadLetterEntry.v1", "task_id": task["task_id"], "tenant_id": task["tenant_id"],
            "capability_id": task["capability_id"], "attempt": task["attempt"], "max_attempts": task["max_attempts"],
            "reason": "max_attempts_or_fatal", "dead_at": task.get("failed_at") or task.get("updated_at", ""),
            "error_json": dict(task.get("error_json", {}))}


def project_idempotency_key(task: dict) -> dict:
    """IdempotencyKey.v1 — the (key -> single live task) mapping that makes enqueue safe to retry."""
    return {"schema_version": "IdempotencyKey.v1", "idempotency_key": task["idempotency_key"],
            "task_id": task["task_id"], "tenant_id": task["tenant_id"], "capability_id": task["capability_id"]}


__all__ = ["project_work_item", "project_worker_claim", "project_ack_nack_receipt", "project_dead_letter",
           "project_idempotency_key", "WORK_ITEM_CORE_FIELDS"]
