#!/usr/bin/env python3
"""scripts.check_worker_telemetry_schema — proof (C-FLEET-2): the telemetry roll-up emits all seven tables
with the fields the schema requires, computed deterministically from the DB ledger, and the values are
coherent (wait/runtime ms, retries, dlq, failure counts, provider rates). Telemetry is a pure read — it
never mutates the ledger.

CLI: PYTHONPATH=. python3 scripts/check_worker_telemetry_schema.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.baltor.workers import telemetry as T
from src.baltor.workers.fleet_ledger import FleetLedger

_SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "workers" / "WorkerTelemetry.schema.json"
T0 = "2026-06-06T00:00:00Z"
CAP = "native.export"


def _scenario() -> FleetLedger:
    L = FleetLedger(); L.register_worker(worker_id="w", capability_ids=[CAP], now=T0)
    # task 1: claim → start → ack (success)
    L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="ok", now=T0, priority_class="P1")
    c = L.claim_task(worker_id="w", capability_id=CAP, now="2026-06-06T00:00:01Z")
    L.start_task(c["task_id"], "w", "2026-06-06T00:00:02Z")
    L.ack_task(c["task_id"], "w", ["art-1"], "2026-06-06T00:00:05Z")
    # task 2: claim → nack with a failure type (retryable) → re-queued
    L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="fail", now=T0, priority_class="P2",
                   max_attempts=1)
    c2 = L.claim_task(worker_id="w", capability_id=CAP, now="2026-06-06T00:00:03Z")
    L.start_task(c2["task_id"], "w", "2026-06-06T00:00:03Z")
    L.nack_task(c2["task_id"], "w", {"failure_type": "rate_limited"}, retryable=False, now="2026-06-06T00:00:04Z")  # → dead
    # task 3: left queued
    L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="wait", now=T0, priority_class="P2")
    return L


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schema = json.loads(_SCHEMA.read_text())
    L = _scenario()
    now = "2026-06-06T00:01:00Z"
    metrics = T.all_metrics(L, now=now)

    chk("all 7 tables present", set(metrics) == set(schema["required"]), str(set(schema["required"]) - set(metrics)))

    # each table's records carry the schema-required fields
    def req(table):
        node = schema["properties"][table]
        return set((node.get("items", node)).get("required", []))

    for table in ("worker_task_metrics", "worker_lifecycle_metrics", "worker_provider_metrics", "worker_failure_metrics"):
        for rec in metrics[table]:
            missing = req(table) - set(rec)
            chk(f"{table} record has required fields", missing == set(), str(missing))
            if missing:
                break
    for table in ("worker_queue_metrics", "worker_cost_metrics", "worker_capacity_snapshots"):
        missing = req(table) - set(metrics[table])
        chk(f"{table} has required fields", missing == set(), str(missing))

    # value coherence
    tasks = {r["task_id"]: r for r in metrics["worker_task_metrics"]}
    ok_task = next(r for r in tasks.values() if r["status"] == "succeeded")
    chk("succeeded task has queue_wait_ms + runtime_ms", ok_task["queue_wait_ms"] == 1000 and ok_task["runtime_ms"] == 3000,
        f"{ok_task['queue_wait_ms']}/{ok_task['runtime_ms']}")
    chk("queue_depth counts the still-queued task", metrics["worker_queue_metrics"]["queue_depth"] == 1)
    chk("dlq_count counts the dead task", metrics["worker_queue_metrics"]["dlq_count"] == 1)
    chk("failure_metrics counts rate_limited", any(f["failure_type"] == "rate_limited" and f["count"] == 1 for f in metrics["worker_failure_metrics"]))
    chk("cost_metrics tasks_succeeded == 1", metrics["worker_cost_metrics"]["tasks_succeeded"] == 1)
    chk("capacity snapshot sees the live worker", metrics["worker_capacity_snapshots"]["live_workers"] == 1)

    # purity: telemetry did not mutate the ledger
    before = len(L._tasks)
    T.all_metrics(L, now=now)
    chk("telemetry is a pure read (no ledger mutation)", len(L._tasks) == before)

    # determinism
    chk("deterministic", json.dumps(T.all_metrics(_scenario(), now=now), sort_keys=True)
        == json.dumps(T.all_metrics(_scenario(), now=now), sort_keys=True))

    print(f"\n{'PASS — check_worker_telemetry_schema: 7 tables with required fields, coherent values (wait/runtime/dlq/failures/cost/capacity), pure read, deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
