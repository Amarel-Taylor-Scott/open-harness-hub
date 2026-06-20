"""src.baltor.workers.supervisor_metrics — LAG metrics for the control-plane supervisor (C-FLEET-3).

The supervisor should scale on COORDINATION pressure, not CPU and not heavy-worker busyness. These
metrics expose that pressure: loop duration vs the tick budget, over-budget ticks, shard lag, and due
backlog. `should_scale_supervisor` turns them into a recommendation (scale the CONTROL PLANE — add a
shard owner / standby — never "do more work in one process"). Pure + deterministic.
"""
from __future__ import annotations

from .fleet_ledger import _age_s

# scale signals — single source
OVER_BUDGET_RATIO = 0.5        # >half of recent ticks over their interval budget ⇒ scale
SHARD_LAG_HIGH_S = 60          # a shard not ticked within this ⇒ its owner is behind/stale
DUE_BACKLOG_HIGH = 50         # due tasks piling up across ticks ⇒ scale


def lag_metrics(ledger, *, now: str) -> dict:
    ticks = ledger.ticks()
    durations = [t["duration_ms"] for t in ticks]
    over_budget = [t for t in ticks if t["interval_ms"] and t["duration_ms"] > t["interval_ms"]]
    # shard lag: seconds since each owned shard's last heartbeat
    shard_lag = {}
    for s in ledger._shards.values():
        if s["owner_id"] and s["heartbeat_at"]:
            shard_lag[s["shard_id"]] = round(_age_s(s["heartbeat_at"], now), 2)
    last_due = ticks[-1]["due_task_count"] if ticks else 0
    return {
        "now": now,
        "tick_count": len(ticks),
        "avg_loop_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "max_loop_duration_ms": max(durations) if durations else 0,
        "over_budget_tick_count": len(over_budget),
        "over_budget_ratio": round(len(over_budget) / len(ticks), 3) if ticks else 0.0,
        "shard_lag_s": shard_lag,
        "max_shard_lag_s": max(shard_lag.values()) if shard_lag else 0.0,
        "latest_due_task_count": last_due,
        "active_instances": sum(1 for i in ledger._instances.values() if i["status"] == "running"),
        "owned_shards": sum(1 for s in ledger._shards.values() if s["status"] == "owned"),
    }


def should_scale_supervisor(metrics: dict) -> dict:
    """Recommend scaling the CONTROL PLANE (more shard owners / a standby), with the reason. Never
    recommends doing heavy work in-process."""
    reasons = []
    if metrics["over_budget_ratio"] >= OVER_BUDGET_RATIO and metrics["tick_count"] >= 2:
        reasons.append(f"tick over budget {metrics['over_budget_ratio']:.0%} ≥ {OVER_BUDGET_RATIO:.0%}")
    if metrics["max_shard_lag_s"] >= SHARD_LAG_HIGH_S:
        reasons.append(f"shard lag {metrics['max_shard_lag_s']}s ≥ {SHARD_LAG_HIGH_S}s")
    if metrics["latest_due_task_count"] >= DUE_BACKLOG_HIGH:
        reasons.append(f"due backlog {metrics['latest_due_task_count']} ≥ {DUE_BACKLOG_HIGH}")
    return {"scale_supervisor": bool(reasons),
            "action": "add_shard_owner_or_standby" if reasons else "steady",
            "reasons": reasons}


__all__ = ["lag_metrics", "should_scale_supervisor"]
