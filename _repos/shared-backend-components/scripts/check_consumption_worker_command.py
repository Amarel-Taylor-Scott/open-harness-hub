#!/usr/bin/env python3
"""scripts.check_consumption_worker_command — proof (C-CONSUME-2): the durable `context.consume` command runs
the governed ingestion→consumption path through ConsumptionService as durable work — a ContextResponse is
recorded durably, a duplicate (same source_snapshot_hash) is idempotent (no double-serve), an invalid command
safe-fails to the DLQ (no worker crash), and two worker processes do not double-serve. Reuses the durable store
+ worker; no second worker framework.

CLI: python3 _repos/shared-backend-components/scripts/check_consumption_worker_command.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.durable_store import DurableStore
from scripts.flywheel_worker import work_once

Q = "runtime.commands"


def _cmd(snap: str, *, corpus: str = "cfpb", tenant: str = "demo") -> dict:
    return {"command_type": "context.consume", "tenant_id": tenant, "corpus": corpus,
            "source_snapshot_hash": snap, "require_optimized": True}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = DurableStore(":memory:")

    # 1) a context.consume command is claimed, run through ConsumptionService, and recorded durably
    store.enqueue(Q, _cmd("snap-1"), idempotency_key="cc-1")
    r = work_once(store, Q, worker_id="w1", now=1000)
    check("worker runs context.consume → served ContextResponse", bool(r and r.get("ok")) and r.get("first_process") is True
          and r.get("decision") == "served" and r.get("served_fact_count", 0) > 0, str(r))
    evs = store.recent_events(limit=200)
    resp_evs = [e for e in evs if e.get("kind") == "context.response.created"]
    check("a ContextResponse is recorded durably", len(resp_evs) == 1 and resp_evs[0]["payload"]["answer"].startswith("10 business days"))
    check("the durable response carries receipt lineage",
          all(resp_evs[0]["payload"]["receipts"].get(k) for k in ("verification_receipt_id", "optimization_receipt_id", "consumption_receipt_id")))

    # 2) a duplicate snapshot is idempotent (no double-serve)
    store.enqueue(Q, _cmd("snap-1"), idempotency_key="cc-1-dup")
    r2 = work_once(store, Q, worker_id="w1", now=1001)
    check("duplicate source_snapshot is idempotent (skipped, not re-served)", bool(r2 and r2.get("ok")) and r2.get("first_process") is False and r2.get("skipped") is True)
    check("still exactly ONE ContextResponse recorded", len([e for e in store.recent_events(limit=200) if e.get("kind") == "context.response.created"]) == 1)

    # 3) an invalid command safe-fails to the DLQ (no crash)
    store.enqueue(Q, {"command_type": "context.consume", "tenant_id": "demo", "corpus": "bogus"}, idempotency_key="cc-bad", max_attempts=5)
    rb = work_once(store, Q, worker_id="w1", now=1002)
    check("invalid context.consume safe-fails (no crash, not acked ok)", isinstance(rb, dict) and rb.get("ok") is False)
    check("invalid context.consume dead-letters immediately (permanent, default budget)", store.stats(Q).get("dead", 0) == 1, str(store.stats(Q)))

    # 4) two worker processes do not double-serve the SAME snapshot
    s2 = DurableStore(":memory:")
    s2.enqueue(Q, _cmd("snap-2"), idempotency_key="k2a")
    s2.enqueue(Q, _cmd("snap-2"), idempotency_key="k2b")  # same snapshot, different idk → both claimable
    a = work_once(s2, Q, worker_id="wA", now=2000)
    b = work_once(s2, Q, worker_id="wB", now=2001)
    served = [x for x in (a, b) if x and x.get("first_process") is True]
    check("two workers serve the same snapshot exactly ONCE", len(served) == 1
          and len([e for e in s2.recent_events(limit=200) if e.get("kind") == "context.response.created"]) == 1, str([a, b]))

    store.close(); s2.close()
    print(f"\n{'PASS — check_consumption_worker_command: context.consume runs the governed path as durable work (response recorded durably with receipt lineage); duplicate idempotent; invalid safe-fails to DLQ; two workers serve a snapshot exactly once.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: context.consume durable worker command.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
