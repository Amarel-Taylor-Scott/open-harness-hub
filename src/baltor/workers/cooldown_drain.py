"""src.baltor.workers.cooldown_drain — COOLDOWN + DRAIN ramp-down behaviour (C-FLEET-2).

A worker that paid the cold-start cost should not die after one task: it enters cooldown, polls compatible
queues, and claims any work that arrives within its keepalive window. Only when no work arrives before the
idle timeout does it shut down — recording cooldown_task_pickup_count and idle_burn_ms so the policy
recommender can later decide whether the policy should keep workers warmer or colder.

Deterministic (injected `now`; advances a fixed step per processed task). Ownership is still ONLY via the
ledger's atomic claim — cooldown does not bypass it.
"""
from __future__ import annotations

from .fleet_ledger import FleetLedger, _plus_s

_STEP_S = 1                 # deterministic time step per processed task in this model


def run_cooldown(ledger: FleetLedger, *, worker_id: str, capability_id: str, now: str,
                 idle_shutdown_seconds: int, queue_names: list | None = None,
                 lease_seconds: int = 60) -> dict:
    """Drain compatible work during cooldown, then shut down on idle. Returns ramp-down metrics."""
    pickups = 0
    cur = now
    ledger.set_worker_status(worker_id, "cooldown", now=cur)
    while True:
        claim = ledger.claim_task(worker_id=worker_id, capability_id=capability_id, now=cur,
                                  queue_names=queue_names, lease_seconds=lease_seconds)
        if claim is None:
            break
        ledger.start_task(claim["task_id"], worker_id, cur)
        ledger.ack_task(claim["task_id"], worker_id, [], cur)
        pickups += 1
        cur = _plus_s(cur, _STEP_S)
    # no more compatible work: the keepalive window is "burned" idle before shutdown
    idle_burn_ms = max(0, idle_shutdown_seconds) * 1000
    stopped_at = _plus_s(cur, max(0, idle_shutdown_seconds))
    ledger.set_worker_status(worker_id, "stopped", now=stopped_at)
    return {
        "worker_id": worker_id,
        "capability_id": capability_id,
        "cooldown_task_pickup_count": pickups,
        "idle_burn_ms": idle_burn_ms,
        "status": "stopped",
        "stopped_at": stopped_at,
    }


__all__ = ["run_cooldown"]
