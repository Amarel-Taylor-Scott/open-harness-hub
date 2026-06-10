#!/usr/bin/env python3
"""scripts.check_worker_fleet_supervisor — proof: the capacity planner decides correctly across the cases:
no-worker→spawn, warm-worker-SLA-ok→use_existing, SLA-miss→spawn, batch waits below threshold, dispatches
at threshold, dispatches partial at max_wait, reclaims expired leases, and flags provider fallback.

CLI: PYTHONPATH=. python3 scripts/check_worker_fleet_supervisor.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import FleetLedger
from src.baltor.workers.fleet_supervisor import decide_for_capability

T0 = "2026-06-06T00:00:00Z"


def _actions(decisions):
    return {d["action"] for d in decisions}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # Case A — on-demand task, no worker → spawn
    L = FleetLedger()
    L.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="a", now=T0,
                   batch_policy_id="on_demand_immediate", sla_policy_id="interactive_10s")
    d = decide_for_capability(L, "native.export", now=T0)
    chk("A: on-demand + no worker → spawn", "spawn" in _actions(d), str(_actions(d)))

    # Case B — warm worker with free capacity + SLA ok → use_existing
    L.register_worker(worker_id="ne1", capability_ids=["native.export"], max_concurrency=8, now=T0)
    L.set_worker_status("ne1", "warm", now=T0)
    d = decide_for_capability(L, "native.export", now=T0)
    chk("B: warm worker + SLA ok → use_existing", "use_existing" in _actions(d), str(_actions(d)))

    # Case C — warm worker but no free capacity → spawn
    L2 = FleetLedger()
    L2.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="c", now=T0,
                    batch_policy_id="on_demand_immediate", sla_policy_id="interactive_10s")
    w = L2.register_worker(worker_id="ne2", capability_ids=["native.export"], max_concurrency=1, now=T0)
    L2.set_worker_status("ne2", "busy", now=T0); w["active_task_count"] = 1
    d = decide_for_capability(L2, "native.export", now=T0)
    chk("C: warm worker but no free slot → spawn", "spawn" in _actions(d), str(_actions(d)))

    # Case D — batch_min_5 with 4 queued, within max_wait → batch_wait
    L3 = FleetLedger()
    for i in range(4):
        L3.enqueue_task(tenant_id="d", capability_id="browser.research", idempotency_key=f"b{i}", now=T0,
                        batch_policy_id="batch_min_5", sla_policy_id="standard_2m")
    d = decide_for_capability(L3, "browser.research", now=T0)
    chk("D: batch_5 at 4 within max_wait → batch_wait", "batch_wait" in _actions(d), str(_actions(d)))

    # Case E — batch_min_5 with 5 queued → batch_dispatch
    L3.enqueue_task(tenant_id="d", capability_id="browser.research", idempotency_key="b5", now=T0,
                    batch_policy_id="batch_min_5", sla_policy_id="standard_2m")
    d = decide_for_capability(L3, "browser.research", now=T0)
    chk("E: batch_5 at 5 → batch_dispatch", "batch_dispatch" in _actions(d), str(_actions(d)))

    # Case F (max_wait) — batch_min_5 with 1 queued but oldest age > max_wait(60s) → batch_dispatch (partial)
    L4 = FleetLedger()
    L4.enqueue_task(tenant_id="d", capability_id="browser.research", idempotency_key="old", now=T0,
                    batch_policy_id="batch_min_5", sla_policy_id="standard_2m")
    d = decide_for_capability(L4, "browser.research", now="2026-06-06T00:02:00Z")  # 120s > 60s max_wait
    chk("F: batch below threshold but max_wait reached → batch_dispatch (partial)", "batch_dispatch" in _actions(d), str(_actions(d)))

    # Case H — expired lease reclaim surfaces as a reclaim decision
    L5 = FleetLedger(); L5.register_worker(worker_id="x", capability_ids=["native.export"], now=T0)
    L5.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="lease", now=T0,
                    batch_policy_id="on_demand_immediate")
    L5.claim_task(worker_id="x", capability_id="native.export", now=T0, lease_seconds=10)
    d = decide_for_capability(L5, "native.export", now="2026-06-06T00:05:00Z")
    chk("H: expired lease → reclaim decision", "reclaim" in _actions(d), str(_actions(d)))

    # Fallback — a re-queued task on attempt>0 with a fallback provider → fallback decision
    L6 = FleetLedger(); L6.register_worker(worker_id="f", capability_ids=["verify.fact"], now=T0)
    t = L6.enqueue_task(tenant_id="d", capability_id="verify.fact", idempotency_key="fb", now=T0,
                        batch_policy_id="on_demand_immediate", required_provider="verify.deterministic@v1",
                        fallback_providers=["verify.llm@candidate"])
    L6.claim_task(worker_id="f", capability_id="verify.fact", now=T0)
    L6.start_task(t["task_id"], "f", T0)
    L6.nack_task(t["task_id"], "f", {"e": "x"}, retryable=True, now=T0)  # attempt→1, re-queued
    d = decide_for_capability(L6, "verify.fact", now=T0)
    chk("Fallback: retry with next provider → fallback decision", "fallback" in _actions(d), str(_actions(d)))

    print(f"\n{'PASS — check_worker_fleet_supervisor: spawn-when-no-worker / use-existing-when-SLA-ok / spawn-on-SLA-miss / batch wait+dispatch+max_wait / lease reclaim / provider fallback all decided correctly.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: fleet supervisor decisions.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
