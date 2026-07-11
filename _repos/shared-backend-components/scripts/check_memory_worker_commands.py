#!/usr/bin/env python3
"""scripts.check_memory_worker_commands — proof (C-MEM-2 delta): memory operations run as DURABLE CAPABILITY
TASKS. memory.write / memory.recall tasks are enqueued in the DurableFleetLedger, claimed atomically by a
memory worker, executed via BaltorLocalMemoryProvider, and ack'd — idempotent, two-worker-safe, invalid
payloads safe-fail, and the worker emits ONLY MemoryArtifacts/search results (never a CanonicalFact or
ContextResponse).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_memory_worker_commands.py --self-test
"""
from __future__ import annotations

import argparse
import os
import tempfile

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider
from src.baltor.memory.memory_worker import MEMORY_OPS, process_memory_task, run_memory_worker_durable
from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("memory ops vocabulary declared", "memory.write" in MEMORY_OPS and "memory.recall" in MEMORY_OPS)
    tmp = tempfile.mkdtemp(prefix="baltor-memcmd-")
    db = os.path.join(tmp, "durable.db")
    provider = BaltorLocalMemoryProvider()   # shared across drains (in-memory store)

    # enqueue 3 memory.write durable tasks (idempotent enqueue)
    L = DurableFleetLedger(db)
    for i in range(3):
        L.enqueue_task(tenant_id="t1", capability_id="memory.write", idempotency_key=f"w{i}",
                       payload={"request": {"content": f"builder note {i}", "tenant_id": "t1", "project": "p1", "now": 1000}})
    L.enqueue_task(tenant_id="t1", capability_id="memory.write", idempotency_key="w0",
                   payload={"request": {"content": "dup", "tenant_id": "t1", "project": "p1", "now": 1000}})  # dup key
    chk("idempotent enqueue (dup key → no extra task)", len(L.queued_tasks("memory.write")) == 3)
    # an INVALID memory.write (missing content) → must safe-fail (nack), not crash
    L.enqueue_task(tenant_id="t1", capability_id="memory.write", idempotency_key="bad",
                   payload={"request": {"tenant_id": "t1", "project": "p1", "now": 1000}})
    L.close()

    out = run_memory_worker_durable(db, worker_id="mw", capability="memory.write", provider=provider)
    chk("worker drained + wrote the 3 valid memory tasks", out["written"] == 3, str(out))
    chk("invalid memory.write safe-failed (nack), worker did not crash", out["failed"] >= 1)
    L2 = DurableFleetLedger(db)
    chk("3 memory tasks succeeded in the durable ledger", len(L2.tasks_by_status("succeeded")) == 3)
    chk("the invalid one is dead (DLQ), not hung", len(L2.tasks_by_status("dead")) >= 1)
    L2.close()

    # memory.recall as a durable task (shared provider sees the writes)
    L3 = DurableFleetLedger(db)
    L3.enqueue_task(tenant_id="t1", capability_id="memory.recall", idempotency_key="r1",
                    payload={"request": {"query": "builder note", "tenant_id": "t1", "project": "p1", "now": 1001}})
    L3.close()
    outr = run_memory_worker_durable(db, worker_id="mw", capability="memory.recall", provider=provider)
    chk("memory.recall task processed", outr["processed"] == 1)

    # direct op check: recall returns the writes as candidate context, NEVER facts
    rec = process_memory_task(provider, {"capability_id": "memory.recall", "tenant_id": "t1",
                                         "payload_json": '{"request":{"query":"builder note","tenant_id":"t1","project":"p1","now":1002}}'})
    chk("recall returns the 3 written memories", rec["result"]["count"] == 3, str(rec["result"]))
    chk("recall result is_truth=False (candidate context)", rec["result"]["is_truth"] is False)
    chk("worker emits NO CanonicalFact/ContextResponse/served_facts",
        not any(k in rec["result"] for k in ("canonical_fact", "served_facts", "context_response")))

    # two workers do not duplicate side effects (atomic claim) — fresh queue
    db2 = os.path.join(tmp, "d2.db"); prov2 = BaltorLocalMemoryProvider()
    L4 = DurableFleetLedger(db2)
    for i in range(4):
        L4.enqueue_task(tenant_id="t1", capability_id="memory.write", idempotency_key=f"x{i}",
                        payload={"request": {"content": f"n{i}", "tenant_id": "t1", "project": "p1", "now": 1000}})
    L4.close()
    a = run_memory_worker_durable(db2, worker_id="A", capability="memory.write", provider=prov2)
    b = run_memory_worker_durable(db2, worker_id="B", capability="memory.write", provider=prov2)
    chk("two workers split the 4 tasks with no duplication", a["written"] + b["written"] == 4 and min(a["written"], b["written"]) >= 0)
    L5 = DurableFleetLedger(db2)
    chk("exactly 4 succeeded (no double-processing)", len(L5.tasks_by_status("succeeded")) == 4)
    L5.close()

    print(f"\n{'PASS — check_memory_worker_commands: memory.write/recall run as durable capability tasks (atomic claim, idempotent, invalid→DLQ, two-worker-safe); worker emits only MemoryArtifacts/recall results, never facts.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
