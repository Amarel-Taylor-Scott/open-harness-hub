"""src.teleon.workers.fleet_ledger — the DB-backed capability-task ledger: the SOURCE OF TRUTH for the
worker fleet. Workers do NOT own a task until an atomic claim succeeds. In-memory + deterministic for
self-tests (injected `now`, hashlib ids, no RNG); the same shape maps to SQLite (BEGIN IMMEDIATE) and later
Postgres (SELECT ... FOR UPDATE SKIP LOCKED) without changing the task/worker contracts.

This is an ADDITIVE capability-task ledger over the existing DurableStore/CommandEnvelope path — NOT a second
event-log/queue framework. Pub/Sub/KEDA are optional wake-up/scale layers later; this DB remains truth.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

EPOCH = "1970-01-01T00:00:00Z"

# task status machine
QUEUED, CLAIMED, RUNNING, SUCCEEDED, FAILED, RETRY_WAIT, DEAD, CANCELLED = (
    "queued", "claimed", "running", "succeeded", "failed", "retry_wait", "dead", "cancelled")
_VALID_TRANSITIONS = {
    QUEUED: {CLAIMED, CANCELLED},
    CLAIMED: {RUNNING, QUEUED, FAILED},          # QUEUED = lease reclaimed
    RUNNING: {SUCCEEDED, FAILED, QUEUED},          # QUEUED = lease reclaimed
    FAILED: {RETRY_WAIT, DEAD},
    RETRY_WAIT: {QUEUED},
}


class FleetLedgerError(Exception):
    pass


def _hid(prefix: str, *parts: Any) -> str:
    return prefix + hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


class FleetLedger:
    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}
        self._workers: dict[str, dict] = {}
        self._attempts: list[dict] = []
        self._transitions: list[dict] = []
        self._idem: dict[str, str] = {}  # idempotency_key -> task_id (non-terminal)

    # ── workers ───────────────────────────────────────────────────────────
    def register_worker(self, *, worker_id: str, capability_ids: list, worker_bucket: str = "",
                        provider_id: str = "", queue_names: list | None = None, resource_class: str = "standard_cpu",
                        max_concurrency: int = 1, shutdown_after_idle_seconds: int = 120, now: str = EPOCH) -> dict:
        w = {"schema_version": "CapabilityWorker.v1", "worker_id": worker_id, "capability_ids": list(capability_ids),
             "worker_bucket": worker_bucket, "provider_id": provider_id, "status": "starting",
             "queue_names": list(queue_names or []), "resource_class": resource_class, "current_task_id": "",
             "active_task_count": 0, "max_concurrency": max_concurrency, "started_at": now, "heartbeat_at": now,
             "last_claim_at": "", "cooldown_until": "", "shutdown_after_idle_seconds": shutdown_after_idle_seconds,
             "total_tasks_processed": 0, "total_failures": 0, "startup_ms": 0, "metadata_json": {}}
        self._workers[worker_id] = w
        return w

    def set_worker_status(self, worker_id: str, status: str, *, now: str = EPOCH, cooldown_until: str = "") -> None:
        w = self._workers[worker_id]; w["status"] = status; w["heartbeat_at"] = now
        if cooldown_until:
            w["cooldown_until"] = cooldown_until

    def heartbeat_worker(self, worker_id: str, now: str) -> None:
        self._workers[worker_id]["heartbeat_at"] = now

    def mark_worker_stale(self, worker_id: str, now: str) -> None:
        self._workers[worker_id]["status"] = "failed"; self._workers[worker_id]["heartbeat_at"] = now

    def live_workers(self, capability_id: str | None = None, *, now: str = EPOCH, stale_after_s: int = 60) -> list[dict]:
        out = []
        for w in self._workers.values():
            if w["status"] in ("stopped", "failed"):
                continue
            if w["heartbeat_at"] and now and _age_s(w["heartbeat_at"], now) > stale_after_s:
                continue
            if capability_id is None or capability_id in w["capability_ids"]:
                out.append(w)
        return out

    # ── tasks ─────────────────────────────────────────────────────────────
    def enqueue_task(self, *, tenant_id: str, capability_id: str, idempotency_key: str, now: str,
                     worker_bucket: str = "", task_type: str = "", priority_class: str = "standard",
                     queue_name: str = "", payload_ref: str = "", required_provider: str = "",
                     fallback_providers: list | None = None, batch_policy_id: str = "on_demand_immediate",
                     lifecycle_policy_id: str = "burst_keepalive", sla_policy_id: str = "standard_2m",
                     max_attempts: int = 3, not_before: str = "", deadline_at: str = "") -> dict:
        # idempotency: a live (non-terminal) task with the same key is NOT duplicated
        if idempotency_key in self._idem:
            return self._tasks[self._idem[idempotency_key]]
        tid = _hid("task-", tenant_id, capability_id, idempotency_key)
        t = {"schema_version": "CapabilityTask.v1", "task_id": tid, "tenant_id": tenant_id,
             "capability_id": capability_id, "worker_bucket": worker_bucket, "task_type": task_type,
             "priority_class": priority_class, "status": QUEUED, "queue_name": queue_name,
             "payload_ref": payload_ref, "idempotency_key": idempotency_key, "required_provider": required_provider,
             "fallback_providers": list(fallback_providers or []), "batch_policy_id": batch_policy_id,
             "lifecycle_policy_id": lifecycle_policy_id, "sla_policy_id": sla_policy_id, "deadline_at": deadline_at,
             "not_before": not_before, "max_attempts": max_attempts, "attempt": 0, "lease_owner": "",
             "lease_until": "", "claimed_at": "", "started_at": "", "heartbeat_at": "", "finished_at": "",
             "failed_at": "", "error_json": {}, "result_artifact_ids": [], "created_at": now, "updated_at": now,
             "progress": {}}
        self._tasks[tid] = t
        self._idem[idempotency_key] = tid
        return t

    def _transition(self, task_id: str, new: str, *, worker_id: str = "", reason: str = "", now: str = EPOCH) -> None:
        t = self._tasks[task_id]; old = t["status"]
        if new not in _VALID_TRANSITIONS.get(old, set()):
            raise FleetLedgerError(f"invalid transition {old}->{new} for {task_id}")
        t["status"] = new; t["updated_at"] = now
        self._transitions.append({"task_id": task_id, "worker_id": worker_id, "previous_status": old,
                                  "new_status": new, "timestamp": now, "reason": reason, "attempt": t["attempt"]})

    def _ready(self, t: dict, capability_id: str, queue_names: list | None, now: str) -> bool:
        return (t["status"] == QUEUED and t["capability_id"] == capability_id
                and (not queue_names or not t["queue_name"] or t["queue_name"] in queue_names)
                and (not t["not_before"] or not now or t["not_before"] <= now))

    def claim_task(self, *, worker_id: str, capability_id: str, now: str, queue_names: list | None = None,
                   lease_seconds: int = 60) -> dict | None:
        """ATOMIC claim: the oldest ready task for this capability → exactly one worker. (SQLite: wrap in
        BEGIN IMMEDIATE; Postgres: SELECT ... FOR UPDATE SKIP LOCKED.)"""
        w = self._workers.get(worker_id)
        if w is not None and capability_id not in w["capability_ids"]:
            raise FleetLedgerError(f"worker {worker_id!r} not registered for capability {capability_id!r}")
        cands = sorted([t for t in self._tasks.values() if self._ready(t, capability_id, queue_names, now)],
                       key=lambda t: (t["created_at"], t["task_id"]))
        if not cands:
            return None
        t = cands[0]
        self._transition(t["task_id"], CLAIMED, worker_id=worker_id, reason="atomic_claim", now=now)
        t["lease_owner"] = worker_id; t["lease_until"] = _plus_s(now, lease_seconds); t["claimed_at"] = now
        if worker_id in self._workers:
            self._workers[worker_id]["last_claim_at"] = now
        self.record_attempt(t["task_id"], worker_id, t.get("required_provider") or self._provider_for(t), CLAIMED)
        return t

    def claim_batch(self, *, worker_id: str, capability_id: str, now: str, batch_min: int,
                    queue_names: list | None = None, lease_seconds: int = 300) -> list[dict]:
        out = []
        while len(out) < batch_min:
            t = self.claim_task(worker_id=worker_id, capability_id=capability_id, now=now,
                                queue_names=queue_names, lease_seconds=lease_seconds)
            if t is None:
                break
            out.append(t)
        return out

    def _provider_for(self, t: dict) -> str:
        order = ([t["required_provider"]] if t["required_provider"] else []) + list(t["fallback_providers"])
        idx = min(t["attempt"], max(0, len(order) - 1)) if order else 0
        return order[idx] if order else ""

    def start_task(self, task_id: str, worker_id: str, now: str) -> dict:
        t = self._tasks[task_id]
        if t["lease_owner"] != worker_id:
            raise FleetLedgerError("start requires the claiming worker")
        self._transition(task_id, RUNNING, worker_id=worker_id, reason="start", now=now)
        t["started_at"] = now; t["heartbeat_at"] = now
        return t

    def update_progress(self, task_id: str, worker_id: str, progress: dict, now: str) -> None:
        t = self._tasks[task_id]
        if t["status"] not in (CLAIMED, RUNNING) or t["lease_owner"] != worker_id:
            raise FleetLedgerError("progress requires a claimed/running task owned by the worker")
        t["progress"] = dict(progress); t["heartbeat_at"] = now; t["updated_at"] = now

    def ack_task(self, task_id: str, worker_id: str, result_artifact_ids: list | None, now: str) -> dict:
        t = self._tasks[task_id]
        if t["lease_owner"] != worker_id:
            raise FleetLedgerError("ack requires the owning worker")
        self._transition(task_id, SUCCEEDED, worker_id=worker_id, reason="ack", now=now)
        t["finished_at"] = now; t["result_artifact_ids"] = list(result_artifact_ids or []); t["lease_until"] = ""
        if worker_id in self._workers:
            self._workers[worker_id]["total_tasks_processed"] += 1
        self.record_attempt(task_id, worker_id, self._provider_for(t), SUCCEEDED)
        return t

    def nack_task(self, task_id: str, worker_id: str, error: dict, *, retryable: bool, now: str) -> dict:
        t = self._tasks[task_id]
        if t["lease_owner"] != worker_id:
            raise FleetLedgerError("nack requires the owning worker")
        self.record_attempt(task_id, worker_id, self._provider_for(t), FAILED)
        self._transition(task_id, FAILED, worker_id=worker_id, reason="nack", now=now)
        t["failed_at"] = now; t["error_json"] = dict(error); t["attempt"] += 1
        if worker_id in self._workers:
            self._workers[worker_id]["total_failures"] += 1
        if (not retryable) or t["attempt"] >= t["max_attempts"]:
            self._transition(task_id, DEAD, worker_id=worker_id, reason="max_attempts_or_fatal", now=now)
        else:
            self._transition(task_id, RETRY_WAIT, worker_id=worker_id, reason="will_retry", now=now)
            self._transition(task_id, QUEUED, worker_id=worker_id, reason="requeued", now=now)
            t["lease_owner"] = ""; t["lease_until"] = ""
        return t

    def reclaim_expired_leases(self, now: str) -> list[str]:
        reclaimed = []
        for t in self._tasks.values():
            if t["status"] in (CLAIMED, RUNNING) and t["lease_until"] and t["lease_until"] < now:
                self._transition(t["task_id"], QUEUED, reason="lease_expired_reclaim", now=now)
                t["lease_owner"] = ""; t["lease_until"] = ""
                reclaimed.append(t["task_id"])
        return reclaimed

    def record_attempt(self, task_id: str, worker_id: str, provider_id: str, status: str) -> None:
        self._attempts.append({"task_id": task_id, "worker_id": worker_id, "provider_id": provider_id, "status": status})

    # ── reads ─────────────────────────────────────────────────────────────
    def task(self, task_id: str) -> dict | None:
        return self._tasks.get(task_id)

    def queued_tasks(self, capability_id: str | None = None) -> list[dict]:
        return [t for t in self._tasks.values() if t["status"] == QUEUED and (capability_id is None or t["capability_id"] == capability_id)]

    def tasks_by_status(self, status: str) -> list[dict]:
        return [t for t in self._tasks.values() if t["status"] == status]

    def attempts(self, task_id: str) -> list[dict]:
        return [a for a in self._attempts if a["task_id"] == task_id]

    def transitions(self, task_id: str) -> list[dict]:
        return [x for x in self._transitions if x["task_id"] == task_id]

    def snapshot(self, *, now: str = EPOCH) -> dict:
        caps = {t["capability_id"] for t in self._tasks.values()} | {c for w in self._workers.values() for c in w["capability_ids"]}
        return {"now": now, "capabilities": {c: {"queued": len(self.queued_tasks(c)),
                                                  "live_workers": len(self.live_workers(c, now=now))} for c in sorted(caps)},
                "dead": len(self.tasks_by_status(DEAD))}


def _age_s(ts_from: str, ts_to: str) -> float:
    return _epoch(ts_to) - _epoch(ts_from)


def _epoch(ts: str) -> float:
    import datetime
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def _plus_s(ts: str, s: int) -> str:
    import datetime
    dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")) + datetime.timedelta(seconds=s)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
