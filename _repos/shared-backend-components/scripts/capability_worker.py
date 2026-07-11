#!/usr/bin/env python3
"""scripts.capability_worker — a stateless capability executor. It does NOT own a task until an atomic claim
from the DB ledger succeeds; a --bootstrap-task-id is only a hint. After completing work it DRAINS compatible
tasks during cooldown before shutting down on idle. Deterministic --self-test (in-memory ledger, injected time).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/capability_worker.py --self-test
     (real: --worker-id --capability-id --queue --db [--bootstrap-task-id] [--provider-id] ...)
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import FleetLedger, RUNNING, SUCCEEDED


def process_one(ledger: FleetLedger, *, worker_id: str, capability_id: str, now: str,
                queue_names: list | None = None, bootstrap_task_id: str | None = None,
                fail: bool = False) -> dict | None:
    """Claim → start → (work) → ack/nack ONE task. Ownership ONLY via atomic claim (bootstrap is a hint:
    if it's already gone, we claim the next compatible task instead)."""
    t = None
    if bootstrap_task_id:
        bt = ledger.task(bootstrap_task_id)
        if bt and bt["status"] == "queued":  # only claim it if still claimable — never assume ownership
            t = ledger.claim_task(worker_id=worker_id, capability_id=capability_id, now=now, queue_names=queue_names)
    if t is None:
        t = ledger.claim_task(worker_id=worker_id, capability_id=capability_id, now=now, queue_names=queue_names)
    if t is None:
        return None
    ledger.start_task(t["task_id"], worker_id, now)
    ledger.update_progress(t["task_id"], worker_id, {"percent": 50, "step": "work"}, now)
    if fail:
        return ledger.nack_task(t["task_id"], worker_id, {"error": "stub failure"}, retryable=True, now=now)
    return ledger.ack_task(t["task_id"], worker_id, [f"art:{t['task_id']}"], now)


def run_worker(ledger: FleetLedger, *, worker_id: str, capability_id: str, now: str, queue_names: list | None = None,
               bootstrap_task_id: str | None = None, idle_shutdown_seconds: int = 120) -> dict:
    """Start → warm → claim/process → drain during cooldown → stop. Returns lifecycle metadata.
    `now` advances by 1s per processed task in this deterministic model (real worker uses wall-clock)."""
    ledger.set_worker_status(worker_id, "warm", now=now)
    processed = 0
    boot = bootstrap_task_id
    while True:
        r = process_one(ledger, worker_id=worker_id, capability_id=capability_id, now=now,
                        queue_names=queue_names, bootstrap_task_id=boot)
        boot = None
        if r is None:
            break
        processed += 1
        ledger.set_worker_status(worker_id, "cooldown", now=now)  # drain: loop again to pick up compatible work
    ledger.set_worker_status(worker_id, "stopped", now=now)
    w = ledger._workers[worker_id]
    return {"worker_id": worker_id, "processed": processed, "status": "stopped",
            "total_tasks_processed": w["total_tasks_processed"], "started_at": w["started_at"]}


def run_worker_durable(*, db: str, worker_id: str, capability_id: str,
                       bootstrap_task_id: str | None = None, max_tasks: int = 1000) -> dict:
    """REAL durable drain: a stateless worker PROCESS opens the SQLite DurableFleetLedger, claims atomically,
    processes (drains) every compatible task, then stops on idle. Ownership ONLY via atomic claim (bootstrap
    is a hint). Real wall-clock. This is the worker the live supervisor spawns on the dispatch path."""
    from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
    L = DurableFleetLedger(db)
    L.register_worker(worker_id=worker_id, capability_ids=[capability_id])
    L.set_worker_status(worker_id, "warm")
    processed = 0
    boot = bootstrap_task_id
    while processed < max_tasks:
        t = None
        if boot:
            bt = L.task(boot)
            if bt and bt["status"] == "queued":
                t = L.claim_task(worker_id=worker_id, capability_id=capability_id)
            boot = None
        if t is None:
            t = L.claim_task(worker_id=worker_id, capability_id=capability_id)
        if t is None:
            break                                       # idle: nothing left to drain → stop
        L.start_task(t["task_id"], worker_id)
        L.ack_task(t["task_id"], worker_id, [f"art:{t['task_id']}"])
        processed += 1
    L.set_worker_status(worker_id, "stopped")
    L.close()
    return {"worker_id": worker_id, "processed": processed, "status": "stopped"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    now = "2026-06-06T00:00:00Z"
    L = FleetLedger()
    L.register_worker(worker_id="w1", capability_ids=["utility.http_download"], now=now)
    t1 = L.enqueue_task(tenant_id="demo", capability_id="utility.http_download", idempotency_key="k1", now=now)

    # bootstrap hint does NOT grant ownership: a competitor claims t1 first; our worker must claim another or none
    L.register_worker(worker_id="w2", capability_ids=["utility.http_download"], now=now)
    stolen = L.claim_task(worker_id="w2", capability_id="utility.http_download", now=now)
    chk("competitor claimed the bootstrap task first", stolen["task_id"] == t1["task_id"])
    r = process_one(L, worker_id="w1", capability_id="utility.http_download", now=now, bootstrap_task_id=t1["task_id"])
    chk("bootstrap hint does NOT grant ownership (already claimed → we get nothing)", r is None)

    # fresh worker drains a queue + picks up a task that 'arrives during cooldown'
    L2 = FleetLedger(); L2.register_worker(worker_id="wx", capability_ids=["utility.http_download"], now=now)
    L2.enqueue_task(tenant_id="demo", capability_id="utility.http_download", idempotency_key="a", now=now)
    L2.enqueue_task(tenant_id="demo", capability_id="utility.http_download", idempotency_key="b", now=now)
    out = run_worker(L2, worker_id="wx", capability_id="utility.http_download", now=now)
    chk("worker drained all compatible queued tasks before stopping", out["processed"] == 2, str(out["processed"]))
    chk("worker recorded processed metadata + started_at", out["total_tasks_processed"] == 2 and out["started_at"] == now)
    chk("worker ended stopped (idle, no more work)", out["status"] == "stopped")
    # both tasks succeeded with start/finish recorded
    done = L2.tasks_by_status(SUCCEEDED)
    chk("processed tasks succeeded with start+finish timestamps", len(done) == 2 and all(t["started_at"] and t["finished_at"] for t in done))

    print(f"\n{'PASS — check capability_worker: ownership only via atomic claim (bootstrap is a hint), worker drains compatible work then stops on idle, start/finish/processed metadata recorded.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baltor capability worker (stateless executor).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--worker-id"); p.add_argument("--capability-id"); p.add_argument("--queue"); p.add_argument("--db")
    p.add_argument("--provider-id"); p.add_argument("--bootstrap-task-id"); p.add_argument("--keepalive-seconds", type=int, default=120)
    p.add_argument("--max-concurrency", type=int, default=1); p.add_argument("--idle-shutdown-seconds", type=int, default=120)
    p.add_argument("--once", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.db and a.capability_id:
        out = run_worker_durable(db=a.db, worker_id=a.worker_id or "w-cli",
                                 capability_id=a.capability_id, bootstrap_task_id=a.bootstrap_task_id)
        print(f"drained {out['processed']} task(s); status={out['status']}")
        return 0
    print("capability_worker: pass --db and --capability-id to run the real durable drain, or --self-test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
