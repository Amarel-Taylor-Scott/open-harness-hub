"""src.baltor.workers.fleet_supervisor — the capacity planner. Reads the DB ledger (queued tasks + live
worker heartbeats), and decides per capability whether to USE an existing worker, SPAWN another, WAIT on a
batch window, DISPATCH a batch, RECLAIM expired leases, or FALL BACK to another provider. It never owns or
processes tasks — workers atomically claim from the ledger. Deterministic (injected `now`).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import math
from pathlib import Path

from .fleet_ledger import FleetLedger, _age_s

_A = _resource("architecture")


def _load(name: str, key: str) -> dict:
    data = json.loads((_A / name).read_text())
    return {p[key]: p for p in data["policies"]} if "policies" in data else {p["capability_id"]: p for p in data["capabilities"]}


def _caps() -> dict:
    return {c["capability_id"]: c for c in json.loads((_A / "worker_capability_registry.json").read_text())["capabilities"]}


def _decision(capability_id, case, action, reason, *, now, spawn_count=0, batch_size=0, task_ids=None, worker_ids=None):
    did = "fdec-" + case + "-" + capability_id
    return {"schema_version": "WorkerFleetSupervisorDecision", "decision_id": did, "capability_id": capability_id,
            "case": case, "action": action, "reason": reason, "spawn_count": spawn_count, "batch_size": batch_size,
            "task_ids": list(task_ids or []), "worker_ids": list(worker_ids or []), "created_at": now}


def _free_capacity(ledger: FleetLedger, capability_id: str, now: str) -> tuple[int, list]:
    live = [w for w in ledger.live_workers(capability_id, now=now) if w["status"] in ("warm", "polling", "cooldown", "starting")]
    cap = sum(max(0, w["max_concurrency"] - w["active_task_count"]) for w in live)
    return cap, live


def decide_for_capability(ledger: FleetLedger, capability_id: str, *, now: str,
                          caps: dict | None = None, batch_pol: dict | None = None, sla_pol: dict | None = None,
                          life_pol: dict | None = None) -> list[dict]:
    caps = caps or _caps()
    batch_pol = batch_pol or _load("worker_batch_policies.json", "batch_policy_id")
    sla_pol = sla_pol or _load("worker_sla_policies.json", "sla_policy_id")
    life_pol = life_pol or _load("worker_lifecycle_policies.json", "lifecycle_policy_id")
    cap = caps.get(capability_id, {})
    decisions: list[dict] = []
    if capability_id not in caps:
        # unknown capability: never spawn a worker for an uncataloged capability (fail safely)
        return [_decision(capability_id, "reject", "reject", "unknown capability — not in worker_capability_registry; no spawn", now=now)]

    # H — reclaim expired leases first (stale workers' tasks return to the queue)
    reclaimed = ledger.reclaim_expired_leases(now)
    if reclaimed:
        decisions.append(_decision(capability_id, "H", "reclaim", f"{len(reclaimed)} expired lease(s) reclaimed", now=now, task_ids=reclaimed))

    queued = sorted(ledger.queued_tasks(capability_id), key=lambda t: t["created_at"])
    if not queued:
        return decisions

    # group by batch policy of the queued tasks (use the first task's policy as the lane policy)
    bp_id = queued[0].get("batch_policy_id", "on_demand_immediate")
    bp = batch_pol.get(bp_id, {"batch_min": 1, "max_wait_seconds": 0})
    sp_id = queued[0].get("sla_policy_id", "standard_2m")
    sp = sla_pol.get(sp_id, {"target_seconds": 120})
    lp_id = queued[0].get("lifecycle_policy_id", cap.get("default_lifecycle_policy_id", "burst_keepalive"))
    lp = life_pol.get(lp_id, {"max_workers": 100})
    max_workers = lp.get("max_workers", 100)
    concurrency = cap.get("max_concurrency_per_worker", 1)
    est_ms = cap.get("estimated_task_ms", 1000)

    # F — fallback: any queued task on a retry (attempt>0) with a next provider available
    fb = [t for t in queued if t["attempt"] > 0 and (len(t.get("fallback_providers", [])) >= t["attempt"])]
    if fb:
        decisions.append(_decision(capability_id, "F", "fallback", "retry with next provider in fallback_order",
                                   now=now, task_ids=[t["task_id"] for t in fb]))

    # BATCH lane (batch_min > 1)
    if bp.get("batch_min", 1) > 1:
        n = len(queued)
        oldest_age = _age_s(queued[0]["created_at"], now) if now else 0
        if n >= bp["batch_min"]:
            decisions.append(_decision(capability_id, "E", "batch_dispatch", f"batch full ({n}>={bp['batch_min']})",
                                       now=now, batch_size=min(n, bp["batch_min"]), task_ids=[t["task_id"] for t in queued[:bp["batch_min"]]], spawn_count=1))
        elif oldest_age >= bp.get("max_wait_seconds", 0) > 0:
            decisions.append(_decision(capability_id, "G", "batch_dispatch", f"max_wait reached ({int(oldest_age)}s); partial batch",
                                       now=now, batch_size=n, task_ids=[t["task_id"] for t in queued], spawn_count=1))
        else:
            decisions.append(_decision(capability_id, "D", "batch_wait", f"batch not full ({n}<{bp['batch_min']}) and within max_wait",
                                       now=now, batch_size=n))
        return decisions

    # ON-DEMAND lane (batch_min == 1)
    free, live = _free_capacity(ledger, capability_id, now)
    sla_ms = sp.get("target_seconds", 120) * 1000
    sla_ok = free >= len(queued) and est_ms <= sla_ms
    if live and sla_ok:
        decisions.append(_decision(capability_id, "B", "use_existing", f"{free} free slot(s) meet SLA ({est_ms}ms<= {sla_ms}ms)",
                                   now=now, worker_ids=[w["worker_id"] for w in live]))
    else:
        deficit = max(1, len(queued) - free)
        spawn = min(max_workers - len(ledger.live_workers(capability_id, now=now)), math.ceil(deficit / max(1, concurrency)))
        spawn = max(0, spawn)
        case = "A" if not live else "C"
        reason = "no live worker" if not live else f"existing workers miss SLA (free={free}, est={est_ms}ms vs {sla_ms}ms)"
        decisions.append(_decision(capability_id, case, "spawn", reason, now=now, spawn_count=spawn or 1,
                                   task_ids=[t["task_id"] for t in queued]))
    return decisions


def tick(ledger: FleetLedger, *, now: str) -> list[dict]:
    """One supervisor pass over every capability with queued work or live workers."""
    caps = _caps()
    seen = {t["capability_id"] for t in ledger.queued_tasks()} | set()
    out: list[dict] = []
    for cid in sorted(seen | set(caps)):
        out.extend(decide_for_capability(ledger, cid, now=now, caps=caps))
    return out
