#!/usr/bin/env python3
"""scripts.check_worker_cooldown_drain — proof (C-FLEET-2): a worker in cooldown drains compatible work
that arrives within its keepalive window (claiming atomically), records cooldown_task_pickup_count and
idle_burn_ms, and shuts down on idle — writing its final worker status. A worker that paid the cold-start
cost is reused; ownership is still only via the ledger's atomic claim.

CLI: PYTHONPATH=. python3 scripts/check_worker_cooldown_drain.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.cooldown_drain import run_cooldown
from src.baltor.workers.fleet_ledger import FleetLedger

T0 = "2026-06-06T00:00:00Z"
CAP = "utility.http_download"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # drain two queued tasks during cooldown
    L = FleetLedger(); L.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="a", now=T0)
    L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="b", now=T0)
    out = run_cooldown(L, worker_id="w", capability_id=CAP, now=T0, idle_shutdown_seconds=90)
    chk("drained both compatible tasks during cooldown", out["cooldown_task_pickup_count"] == 2, str(out["cooldown_task_pickup_count"]))
    chk("recorded idle_burn_ms (keepalive burned before shutdown)", out["idle_burn_ms"] == 90 * 1000, str(out["idle_burn_ms"]))
    chk("ended stopped", out["status"] == "stopped")
    chk("worker status written to stopped", L._workers["w"]["status"] == "stopped")
    chk("both tasks succeeded", len(L.tasks_by_status("succeeded")) == 2, str(len(L.tasks_by_status("succeeded"))))

    # idle worker: nothing to drain → 0 pickups, still records idle burn + stops
    L2 = FleetLedger(); L2.register_worker(worker_id="i", capability_ids=[CAP], now=T0)
    out2 = run_cooldown(L2, worker_id="i", capability_id=CAP, now=T0, idle_shutdown_seconds=60)
    chk("idle worker drains nothing", out2["cooldown_task_pickup_count"] == 0)
    chk("idle worker still records idle_burn + stops", out2["idle_burn_ms"] == 60000 and out2["status"] == "stopped")

    # determinism
    L3 = FleetLedger(); L3.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    L3.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="a", now=T0)
    o3 = run_cooldown(L3, worker_id="w", capability_id=CAP, now=T0, idle_shutdown_seconds=90)
    L4 = FleetLedger(); L4.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    L4.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="a", now=T0)
    o4 = run_cooldown(L4, worker_id="w", capability_id=CAP, now=T0, idle_shutdown_seconds=90)
    chk("deterministic", o3 == o4)

    print(f"\n{'PASS — check_worker_cooldown_drain: cooldown drains compatible work (atomic claim), records pickup_count + idle_burn_ms, writes final status, deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
