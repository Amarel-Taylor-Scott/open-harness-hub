#!/usr/bin/env python3
"""scripts.check_durable_fleet_ledger — proof: the DURABLE (SQLite) FleetLedger upholds the FleetLedger
contract across processes — atomic exactly-one claim, persistence across reopen, idempotent enqueue,
retry/DLQ, lease reclaim — so the live supervisor's spawn pass + multiple worker processes can run against
one durable ledger.

CLI: PYTHONPATH=. python3 scripts/check_durable_fleet_ledger.py --self-test
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger

_REPO = Path(__file__).resolve().parents[1]
T0 = "2026-06-06T00:00:00Z"
CAP = "verify.fact"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-dfl-")
    db = os.path.join(tmp, "durable.db")
    L = DurableFleetLedger(db)
    L.register_worker(worker_id="a", capability_ids=[CAP], now=T0)
    L.register_worker(worker_id="b", capability_ids=[CAP], now=T0)

    # idempotent enqueue
    t1 = L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="k1", now=T0)
    t1b = L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="k1", now=T0)
    chk("idempotent enqueue (no duplicate)", t1["task_id"] == t1b["task_id"] and len(L.queued_tasks(CAP)) == 1)

    # in-process atomic claim: exactly one of two workers wins
    c1 = L.claim_task(worker_id="a", capability_id=CAP, now=T0)
    c2 = L.claim_task(worker_id="b", capability_id=CAP, now=T0)
    chk("atomic claim: exactly one worker wins", c1 is not None and c2 is None)
    chk("claimed task owned by the winner", L.task(t1["task_id"])["lease_owner"] == "a")

    # start + ack
    L.start_task(t1["task_id"], "a", T0)
    L.ack_task(t1["task_id"], "a", ["art-1"], T0)
    chk("ack → succeeded", L.task(t1["task_id"])["status"] == "succeeded")
    chk("worker processed count incremented", L.worker("a")["total_tasks_processed"] == 1)
    chk("non-owner cannot start/ack", _raises(lambda: L.start_task(t1["task_id"], "b", T0)))

    # retry then DLQ
    t2 = L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="k2", now=T0, max_attempts=2)
    L.claim_task(worker_id="a", capability_id=CAP, now=T0); L.start_task(t2["task_id"], "a", T0)
    L.nack_task(t2["task_id"], "a", {"failure_type": "network_error"}, retryable=True, now=T0)
    chk("retryable nack re-queues", L.task(t2["task_id"])["status"] == "queued")
    L.claim_task(worker_id="a", capability_id=CAP, now=T0); L.start_task(t2["task_id"], "a", T0)
    L.nack_task(t2["task_id"], "a", {"failure_type": "network_error"}, retryable=True, now=T0)
    chk("max_attempts → dead (DLQ)", L.task(t2["task_id"])["status"] == "dead")

    # lease reclaim
    t3 = L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="k3", now=T0)
    L.claim_task(worker_id="a", capability_id=CAP, now=T0, lease_seconds=10)
    reclaimed = L.reclaim_expired_leases("2026-06-06T00:05:00Z")
    chk("expired lease reclaimed → re-queued", t3["task_id"] in reclaimed and L.task(t3["task_id"])["status"] == "queued")
    L.close()

    # lease FENCING (self-healing correctness, P4): after a lease EXPIRES and is reclaimed, the formerly-owning
    # worker is fenced OUT — it cannot ack/nack/start (no double-completion / lost update) — while a fresh worker
    # re-claims and completes the task EXACTLY ONCE. (Distinct from the never-owned non-owner guard above: here the
    # worker DID hold the lease, then lost it to the reaper.)
    dbf = os.path.join(tmp, "fence.db")
    F = DurableFleetLedger(dbf)
    F.register_worker(worker_id="a", capability_ids=[CAP], now=T0)
    F.register_worker(worker_id="b", capability_ids=[CAP], now=T0)
    tf = F.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="fence", now=T0)
    cf = F.claim_task(worker_id="a", capability_id=CAP, now=T0, lease_seconds=10)
    F.start_task(tf["task_id"], "a", T0)
    chk("fence: worker a owns the lease before expiry", cf is not None and cf["task_id"] == tf["task_id"])
    F.reclaim_expired_leases("2026-06-06T00:05:00Z")   # the 10s lease is long expired by +5min
    chk("fence: reclaim re-queues the task (re-claimable, not corrupted)", F.task(tf["task_id"])["status"] == "queued")
    chk("fence: STALE worker a cannot ack after reclaim (no double-completion)",
        _raises(lambda: F.ack_task(tf["task_id"], "a", ["stale"], T0)))
    chk("fence: STALE worker a cannot nack or start after reclaim",
        _raises(lambda: F.nack_task(tf["task_id"], "a", {"failure_type": "network_error"}, retryable=True, now=T0))
        and _raises(lambda: F.start_task(tf["task_id"], "a", T0)))
    cf2 = F.claim_task(worker_id="b", capability_id=CAP, now=T0, lease_seconds=60)
    chk("fence: a fresh worker b re-claims the reclaimed task", cf2 is not None and cf2["task_id"] == tf["task_id"])
    chk("fence: STALE worker a still cannot ack (task now owned by b)",
        _raises(lambda: F.ack_task(tf["task_id"], "a", ["stale"], T0)))
    F.start_task(tf["task_id"], "b", T0); F.ack_task(tf["task_id"], "b", ["art-b"], T0)
    chk("fence: worker b completes EXACTLY ONCE → succeeded; stale acks never counted",
        F.task(tf["task_id"])["status"] == "succeeded"
        and F.worker("b")["total_tasks_processed"] == 1 and F.worker("a")["total_tasks_processed"] == 0)
    F.close()

    # RESTART SURVIVAL of an IN-FLIGHT lease (P4): a worker claims+starts a task (RUNNING, lease held), then the
    # PROCESS DIES mid-run (ledger closed, no ack). On restart (ledger reopened on the SAME durable db) the RUNNING
    # task + its lease PERSIST; the reaper reclaims the expired in-flight lease; a fresh worker completes it EXACTLY
    # ONCE; and re-enqueuing the same idempotency_key across the crash never forks a duplicate task.
    dbr = os.path.join(tmp, "restart.db")
    R1 = DurableFleetLedger(dbr)
    R1.register_worker(worker_id="a", capability_ids=[CAP], now=T0)
    tr = R1.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="restart", now=T0)
    R1.claim_task(worker_id="a", capability_id=CAP, now=T0, lease_seconds=10)
    R1.start_task(tr["task_id"], "a", T0)
    chk("restart: task is RUNNING + lease held before the crash", R1.task(tr["task_id"])["status"] == "running")
    R1.close()                                   # ← process dies mid-run (no ack)

    R2 = DurableFleetLedger(dbr)                 # ← restart: reopen the SAME durable db
    chk("restart: in-flight RUNNING task + lease survived the restart (durable)",
        R2.task(tr["task_id"])["status"] == "running" and R2.task(tr["task_id"])["lease_owner"] == "a")
    tr_again = R2.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="restart", now=T0)
    chk("restart: re-enqueue with the same idempotency_key returns the SAME task (no forked duplicate)",
        tr_again["task_id"] == tr["task_id"])
    reclaimed_r = R2.reclaim_expired_leases("2026-06-06T00:05:00Z")   # the 10s in-flight lease is long expired
    chk("restart: reaper reclaims the expired IN-FLIGHT (RUNNING) lease → re-queued",
        tr["task_id"] in reclaimed_r and R2.task(tr["task_id"])["status"] == "queued")
    R2.register_worker(worker_id="b", capability_ids=[CAP], now=T0)
    cbr = R2.claim_task(worker_id="b", capability_id=CAP, now=T0, lease_seconds=60)
    chk("restart: a fresh worker re-claims the recovered task", cbr is not None and cbr["task_id"] == tr["task_id"])
    R2.start_task(tr["task_id"], "b", T0); R2.ack_task(tr["task_id"], "b", ["art-recovered"], T0)
    chk("restart: recovered task completes EXACTLY ONCE → succeeded (no duplicate task forked)",
        R2.task(tr["task_id"])["status"] == "succeeded" and len(R2.queued_tasks(CAP)) == 0)
    R2.close()

    # persistence across reopen
    L2 = DurableFleetLedger(db)
    chk("tasks persist across reopen", L2.task(t1["task_id"])["status"] == "succeeded" and len(L2.queued_tasks(CAP)) == 1)
    L2.close()

    # REAL two-process atomic claim: 3 procs race for 1 task → exactly one wins
    db2 = os.path.join(tmp, "race.db")
    L3 = DurableFleetLedger(db2); L3.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    L3.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="race", now=T0); L3.close()
    one_liner = (
        "import sys;from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger as D;"
        f"l=D({db2!r});t=l.claim_task(worker_id=sys.argv[1],capability_id={CAP!r});"
        "print(t['task_id'] if t else 'NONE');l.close()")
    env = {**os.environ, "PYTHONPATH": str(_REPO)}
    procs = [subprocess.Popen([sys.executable, "-c", one_liner, f"p{i}"], cwd=str(_REPO), env=env,
                              stdout=subprocess.PIPE, text=True) for i in range(3)]
    outs = [p.communicate(timeout=30)[0].strip() for p in procs]
    winners = [o for o in outs if o and o != "NONE"]
    chk("3 processes race → EXACTLY ONE claims the task", len(winners) == 1, str(outs))

    print(f"\n{'PASS — check_durable_fleet_ledger: durable atomic exactly-one claim (in-process + 3-process race), idempotent enqueue, owner-gated start/ack, retry→DLQ, lease reclaim + STALE-worker fencing (reclaimed lease → no double-completion; fresh worker completes exactly once), in-flight RUNNING-lease restart survival (reopen → reaper reclaim → exactly-once recovery; idempotent re-enqueue), persistence across reopen.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _raises(fn) -> bool:
    try:
        fn(); return False
    except Exception:
        return True


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
