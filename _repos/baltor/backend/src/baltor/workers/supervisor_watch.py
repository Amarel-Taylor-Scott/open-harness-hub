"""src.baltor.workers.supervisor_watch — ONE live supervisor coordination step (OPP-supervisor-scaling-live).

Called each interval by `baltor_flywheel.py --watch` so MULTIPLE watch processes coordinate safely against
ONE durable SupervisorStore: heartbeat → claim/renew the leader lease → ensure/claim/renew shards →
reclaim stale shards → run leader-only singleton duties (idempotent) → record a capacity snapshot + a tick.

The DB store is the source of truth. This step DECIDES and RECORDS only; it never executes heavy work and
never claims tasks (workers do that via the task ledger's atomic claim). Best-effort: a coordination error
must never kill the health tick (the caller wraps it).
"""
from __future__ import annotations

import datetime
import time

from .supervisor_store import SupervisorStore

LEADER_LEASE = "global"
# default capacity-planning policy for the live spawn-decision pass (overridable by a richer source later)
_LIFECYCLE = {"startup_budget_ms": 3000, "max_workers": 10}
_BATCH = {"batch_min": 1, "max_wait_seconds": 0}
_SLA = {"target_seconds": 120}


def _now(now: int | None) -> int:
    return int(now) if now is not None else int(time.time())


def _iso(epoch: int) -> str:
    return datetime.datetime.utcfromtimestamp(int(epoch)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _spawn_decisions(store: SupervisorStore, *, supervisor_id: str, owned: list[str], fleet_ledger,
                     iso_now: str, now_epoch: int, db: str | None = None, dispatch: bool = False,
                     tick_id: str = "") -> int:
    """Spawn-decision pass over OWNED capability shards — called every live tick. With no fleet_ledger
    (the bare watchdog has no live task queue) it is a no-op; with one, it snapshots queued tasks per
    capability, runs spawn_decision, and records an IDEMPOTENT spawn decision when work needs a worker.
    When `dispatch` + `db` are set it goes further — it DELEGATES to local_spawn_manager to launch a real
    capability-worker process that drains the durable ledger (the live dispatch path), recording an
    idempotent spawn REQUEST. The supervisor itself executes no heavy work; the spawned worker claims
    atomically + drains."""
    if fleet_ledger is None:
        return 0
    from . import local_spawn_manager, spawn_decision
    caps = set(owned)
    recorded = 0
    for cap in owned:
        queued = fleet_ledger.queued_tasks(cap)
        if not queued:
            continue
        live = fleet_ledger.live_workers(cap, now=iso_now)
        workers = [{"worker_id": w["worker_id"], "status": w["status"], "capability_ids": w["capability_ids"],
                    "available_at": w.get("last_claim_at") or iso_now, "max_concurrency": w["max_concurrency"],
                    "active_task_count": w["active_task_count"]} for w in live]
        tasks = [{"task_id": tk["task_id"], "capability_id": cap, "priority_class": tk["priority_class"],
                  "created_at": tk["created_at"], "deadline_at": tk.get("deadline_at") or None} for tk in queued]
        dec = spawn_decision.decide(capability_id=cap, queued=tasks, workers=workers, now=iso_now,
                                    lifecycle=_LIFECYCLE, batch=_BATCH, sla=_SLA, estimated_runtime_ms=500,
                                    known_capabilities=caps)
        if dec["action"] not in ("spawn_new_worker", "dispatch_partial_batch"):
            continue
        d = store.record_spawn_decision(supervisor_id=supervisor_id, capability_id=cap, action=dec["action"],
                                        idempotency_key=f"spawn:{cap}:{tasks[0]['task_id']}", reason=dec["reason"],
                                        tick_id=tick_id, shard_id=cap)
        recorded += 1
        # LIVE DISPATCH: actually spawn ONE real worker to drain (idempotent; not while one is already live)
        if dispatch and db:
            key = f"req:{cap}:{tasks[0]['task_id']}"
            already = any(r["idempotency_key"] == key for r in store.spawn_requests())
            if not already and not live:
                wid = local_spawn_manager.worker_id_for(cap, tasks[0]["task_id"])
                res = local_spawn_manager.spawn(worker_id=wid, capability_id=cap, queue="", db=db, dry_run=False)
                store.record_spawn_request(supervisor_id=supervisor_id, capability_id=cap, worker_id=wid,
                                           decision_id=d["decision_id"], pid=res.get("pid", 0), dry_run=False,
                                           command=res.get("command"), idempotency_key=key, now=now_epoch)
    return recorded


def step(store: SupervisorStore, *, supervisor_id: str, leader_ttl: int = 30, shard_ttl: int = 30,
         max_shards: int = 14, now: int | None = None, proof_summary: dict | None = None,
         fleet_ledger=None, iso_now: str | None = None, db: str | None = None, dispatch: bool = False,
         execution_backend: bool = False, available_creds: set | None = None,
         provider_health: dict | None = None) -> dict:
    """Run one coordination step for `supervisor_id`. Returns {leader, owned_shards, decisions, tick_id}.

    `execution_backend` routes each owned shard's queued durable work through the ExecutionBackendSelector
    (policy + pricebook + health + creds) → records a switchable ExecutionProviderDecision → drains via the
    CHOSEN LOCAL executor (function emulator / job emulator / worker pool). It is the live dispatch path that
    makes backend choice policy-driven and reversible (local now; k8s/cloud later by config) WITHOUT blocking
    on missing cloud creds — an unconfigured cloud backend falls back to local in the selector. It is the
    DRAINER in this mode, so the raw spawn-and-drain path is disabled while it is on (one drainer per queue)."""
    t = _now(now)
    iso = iso_now or _iso(t)
    store.heartbeat_instance(supervisor_id, now=t)

    # leader lease: claim if unheld/expired, renew if ours (try_claim_leader does both). A standby gets False.
    leader = store.try_claim_leader(lease_name=LEADER_LEASE, supervisor_id=supervisor_id, ttl_seconds=leader_ttl, now=t)

    # shards: make sure the default set exists, reclaim stale, renew ours, then claim more up to the cap
    store.ensure_default_shards(now=t)
    store.expire_stale_shards(now=t)
    owned = store.list_owned_shards(supervisor_id, now=t)
    if owned:
        store.renew_shards(supervisor_id=supervisor_id, shard_ids=owned, ttl_seconds=shard_ttl, now=t)
    if len(owned) < max_shards:
        store.claim_available_shards(supervisor_id=supervisor_id, max_shards=max_shards - len(owned),
                                     ttl_seconds=shard_ttl, now=t)
    owned = store.list_owned_shards(supervisor_id, now=t)

    # leader-only singleton duty — idempotent per scheduling window so it is never duplicated, even if a
    # buggy standby tried to run it (the leader guard PLUS the unique idempotency key are both enforced).
    decisions = 0
    if leader:
        window = t // max(1, leader_ttl)
        store.record_decision(supervisor_id=supervisor_id, decision_type="singleton_proof_sweep",
                              idempotency_key=f"singleton:proof_sweep:{window}",
                              reason="leader-only singleton duty (proof/freshness sweep)", now=t)
        decisions += 1

    # SPAWN-DECISION pass — called EVERY tick over owned capability shards (no-op when no live task queue).
    # In execution_backend mode the selector-driven executor is the drainer, so the spawn pass records
    # capacity DECISIONS only (dispatch=False) — never a second drainer on the same queue.
    decisions += _spawn_decisions(store, supervisor_id=supervisor_id, owned=owned, fleet_ledger=fleet_ledger,
                                  iso_now=iso, now_epoch=t, db=db, dispatch=(dispatch and not execution_backend))

    # EXECUTION-BACKEND DISPATCH (live path) — per owned shard with queued work: select_backend → record a
    # switchable ExecutionProviderDecision → drain via the chosen LOCAL executor. Cloud stays deferred (the
    # selector falls back to local when a cloud backend is unconfigured/unhealthy), so this never blocks.
    execution_dispatched: list[dict] = []
    if execution_backend and db and owned:
        from . import execution_dispatch
        execution_dispatched = execution_dispatch.dispatch_owned_shards(
            store, db, owned=owned, now=t, run=True,
            available_creds=available_creds, provider_health=provider_health)
        decisions += len(execution_dispatched)

    # capacity snapshot (lag accounting / projection)
    snap = store.record_capacity_snapshot(supervisor_id=supervisor_id, now=t,
                                          worker_counts={}, queue_depths={})
    pc = (proof_summary or {}).get("total", 0)
    gc = (proof_summary or {}).get("green_count", 0)
    tick = store.record_tick(supervisor_id=supervisor_id, leader=leader, shard_ids=owned, started_at=t,
                             proof_count=pc, green_count=gc, red_count=max(0, pc - gc),
                             decision_count=decisions)
    return {"leader": leader, "owned_shards": owned, "decisions": decisions,
            "tick_id": tick["tick_id"], "snapshot_id": snap["snapshot_id"],
            "execution_dispatched": execution_dispatched}


__all__ = ["step", "LEADER_LEASE"]
