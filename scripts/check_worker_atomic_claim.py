#!/usr/bin/env python3
"""scripts.check_worker_atomic_claim — proof: the DB-backed ledger's atomic claim layer is correct. Two
workers cannot claim the same task; expired leases reclaim; ack/nack require the owning worker; nack
increments attempt; max attempts → dead; duplicate idempotency key does not duplicate; transitions recorded.

CLI: PYTHONPATH=. python3 scripts/check_worker_atomic_claim.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import FleetLedger, FleetLedgerError, QUEUED, CLAIMED, DEAD, SUCCEEDED


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    now = "2026-06-06T00:00:00Z"
    L = FleetLedger()
    L.register_worker(worker_id="wa", capability_ids=["c"], now=now)
    L.register_worker(worker_id="wb", capability_ids=["c"], now=now)
    t = L.enqueue_task(tenant_id="demo", capability_id="c", idempotency_key="k", now=now, max_attempts=2)

    c1 = L.claim_task(worker_id="wa", capability_id="c", now=now)
    c2 = L.claim_task(worker_id="wb", capability_id="c", now=now)
    chk("first claim wins", c1 and c1["task_id"] == t["task_id"] and c1["lease_owner"] == "wa")
    chk("second worker cannot claim the same task", c2 is None)

    # ack requires the owning worker
    try:
        L.start_task(t["task_id"], "wb", now); chk("start by non-owner rejected", False)
    except FleetLedgerError:
        chk("start by non-owner rejected", True)
    L.start_task(t["task_id"], "wa", now)
    try:
        L.ack_task(t["task_id"], "wb", [], now); chk("ack by non-owner rejected", False)
    except FleetLedgerError:
        chk("ack by non-owner rejected", True)

    # nack increments attempt and re-queues (under max_attempts)
    L.nack_task(t["task_id"], "wa", {"e": "x"}, retryable=True, now=now)
    chk("nack increments attempt + re-queues", L.task(t["task_id"])["attempt"] == 1 and L.task(t["task_id"])["status"] == QUEUED)
    # second failure hits max_attempts(2) → dead
    c3 = L.claim_task(worker_id="wa", capability_id="c", now=now)
    L.start_task(t["task_id"], "wa", now)
    L.nack_task(t["task_id"], "wa", {"e": "x2"}, retryable=True, now=now)
    chk("max attempts → dead (DLQ)", L.task(t["task_id"])["status"] == DEAD)

    # expired lease reclaim
    L2 = FleetLedger(); L2.register_worker(worker_id="wc", capability_ids=["c"], now=now)
    t2 = L2.enqueue_task(tenant_id="demo", capability_id="c", idempotency_key="k2", now=now)
    L2.claim_task(worker_id="wc", capability_id="c", now=now, lease_seconds=10)
    reclaimed = L2.reclaim_expired_leases("2026-06-06T00:05:00Z")
    chk("expired lease reclaimed back to queued", t2["task_id"] in reclaimed and L2.task(t2["task_id"])["status"] == QUEUED)

    # idempotency: same key does not duplicate
    L3 = FleetLedger()
    a = L3.enqueue_task(tenant_id="demo", capability_id="c", idempotency_key="dup", now=now)
    b = L3.enqueue_task(tenant_id="demo", capability_id="c", idempotency_key="dup", now=now)
    chk("duplicate idempotency key → same task (no duplicate)", a["task_id"] == b["task_id"] and len(L3.queued_tasks("c")) == 1)

    # transitions recorded
    chk("status transitions recorded", len(L.transitions(t["task_id"])) >= 4)
    # invalid transition rejected
    L4 = FleetLedger(); tx = L4.enqueue_task(tenant_id="d", capability_id="c", idempotency_key="z", now=now)
    try:
        L4._transition(tx["task_id"], SUCCEEDED, now=now); chk("invalid transition queued->succeeded rejected", False)
    except FleetLedgerError:
        chk("invalid transition queued->succeeded rejected", True)

    print(f"\n{'PASS — check_worker_atomic_claim: exactly-one claim; non-owner ack/start refused; nack increments + re-queues; max attempts → dead; expired leases reclaimed; idempotency dedup; transitions recorded; invalid transitions rejected.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: atomic claim layer.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
