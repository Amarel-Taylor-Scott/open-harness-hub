"""src.baltor.workers.control_plane — one COMPOSED control-plane tick (C-FLEET-3 + C-FLEET-2 glue).

This is the integration that makes the pieces work together as the always-on control plane:

  1. acquire/refresh the leader lease (singleton-duty guard)               [supervisor_ledger]
  2. for each owned capability shard, scan the DB task ledger queue        [fleet_ledger]
  3. consult the spawn-decision engine using that capability's policies    [spawn_decision]
  4. record an IDEMPOTENT spawn decision per due task (no duplicate spawn)  [supervisor_ledger]
  5. record the tick for lag accounting (coordination-pressure metrics)    [supervisor_ledger]

It DECIDES and RECORDS only — it never executes heavy work; workers still claim atomically from the task
ledger. Deterministic (injected `now`). Policies are read from their single-source JSON files. Running
multiple supervisors over the same shard is safe: leader lease + idempotent decisions guarantee no
duplicate spawn.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import spawn_decision

_A = Path(__file__).resolve().parents[3] / "architecture"


def _load(name: str, key: str) -> dict:
    return {p[key]: p for p in json.loads((_A / name).read_text())["policies"]}


def _caps() -> dict:
    return {c["capability_id"]: c for c in json.loads((_A / "worker_capability_registry.json").read_text())["capabilities"]}


def control_plane_tick(*, supervisor_ledger, fleet_ledger, supervisor_id: str, now: str,
                       owned_shards: list[str], lease_name: str = "global", ttl_seconds: int = 30,
                       interval_ms: int = 10000, tick_duration_ms: int = 100) -> dict:
    """Run one control-plane tick for `supervisor_id` over the capability shards it owns."""
    caps = _caps()
    life = _load("worker_lifecycle_policies.json", "lifecycle_policy_id")
    batch = _load("worker_batch_policies.json", "batch_policy_id")
    sla = _load("worker_sla_policies.json", "sla_policy_id")

    is_leader = supervisor_ledger.acquire_lease(lease_name=lease_name, owner_id=supervisor_id, now=now, ttl_seconds=ttl_seconds)
    decisions: list[dict] = []
    due = 0
    for cap in owned_shards:
        c = caps.get(cap, {})
        queued = fleet_ledger.queued_tasks(cap)
        due += len(queued)
        if not queued:
            continue
        lp = life.get(c.get("default_lifecycle_policy_id", "burst_keepalive"), {})
        bp = batch.get(c.get("default_batch_policy_id", "on_demand_immediate"), {"batch_min": 1, "max_wait_seconds": 0})
        sp = sla.get(c.get("default_sla_policy_id", "standard_2m"), {"target_seconds": 120})
        workers = [{"worker_id": w["worker_id"], "status": w["status"], "capability_ids": w["capability_ids"],
                    "available_at": w.get("last_claim_at") or now, "max_concurrency": w["max_concurrency"],
                    "active_task_count": w["active_task_count"]} for w in fleet_ledger.live_workers(cap, now=now)]
        tasks = [{"task_id": t["task_id"], "capability_id": cap, "priority_class": t["priority_class"],
                  "created_at": t["created_at"], "deadline_at": t.get("deadline_at") or None} for t in queued]
        dec = spawn_decision.decide(
            capability_id=cap, queued=tasks, workers=workers, now=now, lifecycle=lp, batch=bp, sla=sp,
            estimated_runtime_ms=c.get("estimated_task_ms", 1000),
            max_concurrency_per_worker=c.get("max_concurrency_per_worker", 1), known_capabilities=set(caps))
        if dec["action"] in ("spawn_new_worker", "dispatch_partial_batch"):
            key = f"spawn:{cap}:{tasks[0]['task_id']}"   # one spawn intent per oldest due task
            decisions.append(supervisor_ledger.record_decision(
                supervisor_id=supervisor_id, decision_type="spawn_worker", idempotency_key=key,
                shard_id=f"shard:{cap}", reason=dec["reason"], output_command_ids=[], now=now))
    supervisor_ledger.record_tick(supervisor_id=supervisor_id, started_at=now, duration_ms=tick_duration_ms,
                                  due_task_count=due, scheduled_count=len(decisions), interval_ms=interval_ms)
    return {"supervisor_id": supervisor_id, "is_leader": is_leader, "decisions": decisions, "due_task_count": due}


__all__ = ["control_plane_tick"]
