"""src.baltor.workers.spawn_decision — the SPAWN DECISION ENGINE (C-FLEET-2).

A pure, deterministic capacity-planning core: given the queued tasks for a capability, the live workers,
the lifecycle/batch/SLA policies, concurrency limits, and provider circuit state, decide ONE of:

  use_existing_worker · spawn_new_worker · wait_for_batch · dispatch_partial_batch ·
  route_to_fallback_provider · hold_due_to_concurrency_limit · dead_letter_invalid

This is the formula the fleet supervisor consults — NOT a second framework. It operates on plain dicts
(no ledger/process dependency) so it is trivially testable and reproducible. Time is injected (`now`).

Estimate-based reuse-vs-spawn (the heart of ramp-up):
    estimated_existing_finish = earliest_free_worker_available_at + runtime
    estimated_new_finish      = now + startup_budget + runtime
Spawn when no existing worker can meet the deadline; reuse when one can.
"""
from __future__ import annotations

from .fleet_ledger import _age_s, _epoch

# decision action vocabulary — single source (imported by the supervisor + proofs)
ACTIONS = (
    "use_existing_worker", "spawn_new_worker", "wait_for_batch", "dispatch_partial_batch",
    "route_to_fallback_provider", "hold_due_to_concurrency_limit", "dead_letter_invalid",
)
_HIGH_PRIORITIES = ("P0", "P1")          # never wait for a batch
_SAFETY_MARGIN_MS = 500                   # spawn only if it beats reuse by more than this


def _decision(action: str, reason: str, **extra) -> dict:
    assert action in ACTIONS, action
    return {"action": action, "reason": reason, **extra}


def _free_workers(workers: list[dict], capability_id: str) -> list[dict]:
    return [w for w in workers
            if capability_id in w.get("capability_ids", [])
            and w.get("status") in ("warm", "polling", "cooldown", "starting", "busy")
            and w.get("max_concurrency", 1) - w.get("active_task_count", 0) > 0]


def decide(*, capability_id: str, queued: list[dict], workers: list[dict], now: str,
           lifecycle: dict, batch: dict, sla: dict,
           estimated_runtime_ms: int, max_concurrency_per_worker: int = 1,
           known_capabilities: set | None = None,
           tenant_active: int = 0, tenant_limit: int | None = None,
           domain_active: int = 0, domain_limit: int | None = None,
           circuit_open: bool = False, has_fallback: bool = False) -> dict:
    """Decide the single best action for `capability_id`'s queued work right now."""
    # dead-letter: capability not cataloged
    if known_capabilities is not None and capability_id not in known_capabilities:
        return _decision("dead_letter_invalid", f"unknown capability {capability_id!r} — not cataloged")
    if not queued:
        return _decision("use_existing_worker", "no queued work", worker_ids=[w["worker_id"] for w in _free_workers(workers, capability_id)])

    # provider circuit open → route to a fallback provider (if one exists), else hold
    if circuit_open:
        if has_fallback:
            return _decision("route_to_fallback_provider", "primary provider circuit is open; route to fallback",
                             task_ids=[t["task_id"] for t in queued])
        return _decision("hold_due_to_concurrency_limit", "primary circuit open and no fallback available — hold")

    # concurrency caps (tenant / domain) — do not spawn past the limit
    if tenant_limit is not None and tenant_active >= tenant_limit:
        return _decision("hold_due_to_concurrency_limit", f"tenant concurrency limit reached ({tenant_active}/{tenant_limit})")
    if domain_limit is not None and domain_active >= domain_limit:
        return _decision("hold_due_to_concurrency_limit", f"domain concurrency limit reached ({domain_active}/{domain_limit})")

    ordered = sorted(queued, key=lambda t: t.get("created_at", ""))
    n = len(ordered)
    batch_min = batch.get("batch_min", 1)
    max_wait = batch.get("max_wait_seconds", 0)
    has_high = any(t.get("priority_class") in _HIGH_PRIORITIES for t in ordered)

    # BATCH lane (batch_min > 1) — but P0/P1 never wait for a batch
    if batch_min > 1 and not has_high:
        oldest_age = _age_s(ordered[0].get("created_at", now), now)
        if n >= batch_min:
            return _decision("spawn_new_worker", f"batch full ({n}>={batch_min}); dispatch a batch worker",
                             batch_size=batch_min, task_ids=[t["task_id"] for t in ordered[:batch_min]], spawn_count=1)
        if max_wait > 0 and oldest_age >= max_wait:
            return _decision("dispatch_partial_batch", f"max_wait reached ({int(oldest_age)}s>={max_wait}s); partial batch",
                             batch_size=n, task_ids=[t["task_id"] for t in ordered])
        return _decision("wait_for_batch", f"batch not full ({n}<{batch_min}) and within max_wait ({int(oldest_age)}s<{max_wait}s)",
                         batch_size=n)

    # ON-DEMAND lane (batch_min == 1, or a high-priority task forcing immediate handling)
    free = _free_workers(workers, capability_id)
    startup_ms = lifecycle.get("startup_budget_ms", 5000)
    sla_ms = sla.get("target_seconds", 120) * 1000

    # earliest an EXISTING free worker could finish vs a NEW worker
    est_existing_finish = None
    if free:
        earliest_avail = min(_epoch(w.get("available_at", now)) for w in free)
        est_existing_finish = (earliest_avail - _epoch(now)) * 1000 + estimated_runtime_ms
    est_new_finish = startup_ms + estimated_runtime_ms

    # deadline: prefer the tightest explicit deadline, else the SLA target
    deadline_ms = sla_ms
    deadlines = [(_epoch(t["deadline_at"]) - _epoch(now)) * 1000 for t in ordered if t.get("deadline_at")]
    if deadlines:
        deadline_ms = min(deadline_ms, min(deadlines))

    existing_meets = est_existing_finish is not None and est_existing_finish <= deadline_ms and estimated_runtime_ms <= deadline_ms
    if existing_meets:
        return _decision("use_existing_worker",
                         f"existing worker finishes in ~{int(est_existing_finish)}ms <= deadline {int(deadline_ms)}ms",
                         worker_ids=[w["worker_id"] for w in free],
                         est_existing_finish_ms=int(est_existing_finish), deadline_ms=int(deadline_ms))

    # otherwise spawn — either no worker, or existing would miss the deadline / be slower than a fresh one
    reason = ("no live worker for capability" if not free
              else f"existing miss deadline (existing ~{int(est_existing_finish)}ms vs new ~{int(est_new_finish)}ms, deadline {int(deadline_ms)}ms)")
    deficit = max(1, n - sum(max(0, w.get("max_concurrency", 1) - w.get("active_task_count", 0)) for w in free))
    spawn = max(1, -(-deficit // max(1, max_concurrency_per_worker)))     # ceil
    spawn = min(spawn, lifecycle.get("max_workers", 100) - len(workers)) or 1
    return _decision("spawn_new_worker", reason, spawn_count=max(1, spawn),
                     task_ids=[t["task_id"] for t in ordered],
                     est_new_finish_ms=int(est_new_finish), deadline_ms=int(deadline_ms))


__all__ = ["decide", "ACTIONS"]
