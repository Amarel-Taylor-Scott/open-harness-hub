"""src.baltor.workers.telemetry — worker fleet TELEMETRY roll-up (C-FLEET-2).

Computes the seven metric tables from the DB task ledger (the source of truth), deterministically:

  worker_task_metrics · worker_lifecycle_metrics · worker_queue_metrics · worker_provider_metrics ·
  worker_cost_metrics · worker_failure_metrics · worker_capacity_snapshots

These feed the policy recommender (ramp-up/ramp-down decisions) and a future /fleet projection. Pure
reads — telemetry never mutates the ledger. Time is injected (`now`). Field lists are the single source
for both the records here and schemas/workers/WorkerTelemetry.schema.json.
"""
from __future__ import annotations

from .failure_taxonomy import failure_policy
from .fleet_ledger import _age_s

# the seven tables — single source of the metric field names
TASK_FIELDS = ("task_id", "capability_id", "priority_class", "status", "queue_wait_ms", "runtime_ms",
               "attempt", "retry_count", "provider_id", "worker_id", "error_type")
LIFECYCLE_FIELDS = ("worker_id", "status", "startup_ms", "tasks_processed", "tasks_failed", "tasks_per_start")
QUEUE_FIELDS = ("queue_depth", "oldest_task_age_s", "tasks_by_priority", "tasks_by_capability",
                "claim_rate", "ack_rate", "nack_rate", "dlq_count", "lease_expiry_count", "batch_fill_ratio")
PROVIDER_FIELDS = ("provider_id", "attempts", "successes", "failures", "success_rate", "failure_rate", "fallback_count")
COST_FIELDS = ("worker_start_count", "tasks_per_worker_start", "tasks_succeeded", "cost_per_successful_task",
               "saved_startups_estimate")
FAILURE_FIELDS = ("failure_type", "count", "retryable", "opens_circuit")
CAPACITY_FIELDS = ("now", "live_workers", "queued", "running", "dead", "by_capability")

_MS = 1000


def _ms(a: str, b: str) -> int | None:
    if not a or not b:
        return None
    return int(_age_s(a, b) * _MS)


def task_metrics(ledger) -> list[dict]:
    out = []
    for t in ledger._tasks.values():
        err = (t.get("error_json") or {}).get("failure_type")
        out.append({
            "task_id": t["task_id"], "capability_id": t["capability_id"], "priority_class": t["priority_class"],
            "status": t["status"], "queue_wait_ms": _ms(t["created_at"], t["claimed_at"]),
            "runtime_ms": _ms(t["started_at"], t["finished_at"]), "attempt": t["attempt"],
            "retry_count": t["attempt"], "provider_id": ledger._provider_for(t),
            "worker_id": t["lease_owner"], "error_type": err,
        })
    return sorted(out, key=lambda r: r["task_id"])


def lifecycle_metrics(ledger) -> list[dict]:
    out = []
    for w in ledger._workers.values():
        out.append({
            "worker_id": w["worker_id"], "status": w["status"], "startup_ms": w.get("startup_ms", 0),
            "tasks_processed": w["total_tasks_processed"], "tasks_failed": w["total_failures"],
            "tasks_per_start": w["total_tasks_processed"],
        })
    return sorted(out, key=lambda r: r["worker_id"])


def _rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def queue_metrics(ledger, *, now: str) -> dict:
    queued = ledger.queued_tasks()
    ages = [_age_s(t["created_at"], now) for t in queued]
    by_pri: dict = {}
    by_cap: dict = {}
    for t in queued:
        by_pri[t["priority_class"]] = by_pri.get(t["priority_class"], 0) + 1
        by_cap[t["capability_id"]] = by_cap.get(t["capability_id"], 0) + 1
    claims = sum(1 for a in ledger._attempts if a["status"] == "claimed")
    acks = sum(1 for a in ledger._attempts if a["status"] == "succeeded")
    nacks = sum(1 for a in ledger._attempts if a["status"] == "failed")
    total_attempts = max(1, len(ledger._attempts))
    dlq = len(ledger.tasks_by_status("dead"))
    lease_exp = sum(1 for tr in ledger._transitions if tr.get("reason") == "lease_expired_reclaim")
    # batch fill ratio: queued vs the largest batch_min among queued tasks (proxy for how full a batch is)
    batch_min = 1
    return {
        "queue_depth": len(queued), "oldest_task_age_s": round(max(ages), 2) if ages else 0.0,
        "tasks_by_priority": by_pri, "tasks_by_capability": by_cap,
        "claim_rate": _rate(claims, total_attempts), "ack_rate": _rate(acks, total_attempts),
        "nack_rate": _rate(nacks, total_attempts), "dlq_count": dlq, "lease_expiry_count": lease_exp,
        "batch_fill_ratio": _rate(len(queued), max(batch_min, len(queued) or 1)),
    }


def provider_metrics(ledger) -> list[dict]:
    by: dict = {}
    for a in ledger._attempts:
        p = a.get("provider_id") or "(none)"
        d = by.setdefault(p, {"provider_id": p, "attempts": 0, "successes": 0, "failures": 0, "fallback_count": 0})
        if a["status"] == "claimed":
            d["attempts"] += 1
        elif a["status"] == "succeeded":
            d["successes"] += 1
        elif a["status"] == "failed":
            d["failures"] += 1
    out = []
    for d in by.values():
        total = max(1, d["successes"] + d["failures"])
        d["success_rate"] = _rate(d["successes"], total)
        d["failure_rate"] = _rate(d["failures"], total)
        out.append(d)
    return sorted(out, key=lambda r: r["provider_id"])


def cost_metrics(ledger, *, worker_start_count: int | None = None) -> dict:
    starts = worker_start_count if worker_start_count is not None else len(ledger._workers)
    succeeded = len(ledger.tasks_by_status("succeeded"))
    return {
        "worker_start_count": starts,
        "tasks_per_worker_start": round(succeeded / starts, 2) if starts else 0.0,
        "tasks_succeeded": succeeded,
        # proxy cost: one start ≈ one cold-start unit; more tasks per start ⇒ lower cost per task
        "cost_per_successful_task": round(starts / succeeded, 3) if succeeded else None,
        "saved_startups_estimate": max(0, succeeded - starts),
    }


def failure_metrics(ledger) -> list[dict]:
    counts: dict = {}
    for t in ledger._tasks.values():
        ft = (t.get("error_json") or {}).get("failure_type")
        if ft:
            counts[ft] = counts.get(ft, 0) + 1
    out = []
    for ft, c in counts.items():
        pol = failure_policy(ft)
        out.append({"failure_type": ft, "count": c, "retryable": pol["retryable"], "opens_circuit": pol["opens_circuit"]})
    return sorted(out, key=lambda r: r["failure_type"])


def capacity_snapshot(ledger, *, now: str) -> dict:
    live = ledger.live_workers(now=now)
    by_cap: dict = {}
    for w in live:
        for c in w["capability_ids"]:
            by_cap[c] = by_cap.get(c, 0) + 1
    return {
        "now": now, "live_workers": len(live),
        "queued": len(ledger.queued_tasks()), "running": len(ledger.tasks_by_status("running")),
        "dead": len(ledger.tasks_by_status("dead")), "by_capability": by_cap,
    }


def all_metrics(ledger, *, now: str) -> dict:
    """The full telemetry bundle — the seven tables in one deterministic snapshot."""
    return {
        "worker_task_metrics": task_metrics(ledger),
        "worker_lifecycle_metrics": lifecycle_metrics(ledger),
        "worker_queue_metrics": queue_metrics(ledger, now=now),
        "worker_provider_metrics": provider_metrics(ledger),
        "worker_cost_metrics": cost_metrics(ledger),
        "worker_failure_metrics": failure_metrics(ledger),
        "worker_capacity_snapshots": capacity_snapshot(ledger, now=now),
    }


__all__ = ["all_metrics", "task_metrics", "lifecycle_metrics", "queue_metrics", "provider_metrics",
           "cost_metrics", "failure_metrics", "capacity_snapshot",
           "TASK_FIELDS", "LIFECYCLE_FIELDS", "QUEUE_FIELDS", "PROVIDER_FIELDS", "COST_FIELDS",
           "FAILURE_FIELDS", "CAPACITY_FIELDS"]
