#!/usr/bin/env python3
"""scripts.check_worker_fleet_supervisor_full_stack — proof: the capability-aware worker fleet holds
end-to-end across the owner's scenarios. Prints SCENARIO | TASKS | WORKERS | DECISION | RESULT | STATUS.

CLI: PYTHONPATH=. python3 scripts/check_worker_fleet_supervisor_full_stack.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import FleetLedger, SUCCEEDED, DEAD
from src.baltor.workers.fleet_supervisor import decide_for_capability
from scripts.capability_worker import run_worker

T0 = "2026-06-06T00:00:00Z"


def _act(ledger, cap, now=T0):
    return [d["action"] for d in decide_for_capability(ledger, cap, now=now)]


def _self_test() -> int:
    fails: list[str] = []
    rows: list[tuple] = []

    def scen(label, tasks, workers, decision, result, ok):
        rows.append((label, tasks, workers, decision, result, "GREEN" if ok else "RED"))
        if not ok:
            fails.append(label)

    # 1 on-demand, no worker -> spawn
    L = FleetLedger(); L.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="1", now=T0, batch_policy_id="on_demand_immediate", sla_policy_id="interactive_10s")
    scen("on-demand,no worker", 1, 0, "spawn", "spawn", "spawn" in _act(L, "native.export"))
    # 2 on-demand, warm worker SLA ok -> use_existing
    L.register_worker(worker_id="ne", capability_ids=["native.export"], max_concurrency=8, now=T0); L.set_worker_status("ne", "warm", now=T0)
    scen("on-demand,warm SLA ok", 1, 1, "use_existing", "reuse", "use_existing" in _act(L, "native.export"))
    # 3 on-demand, warm worker SLA miss -> spawn
    L3 = FleetLedger(); L3.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="3", now=T0, batch_policy_id="on_demand_immediate", sla_policy_id="interactive_10s")
    w = L3.register_worker(worker_id="nf", capability_ids=["native.export"], max_concurrency=1, now=T0); L3.set_worker_status("nf", "busy", now=T0); w["active_task_count"] = 1
    scen("on-demand,SLA miss", 1, 1, "spawn", "spawn", "spawn" in _act(L3, "native.export"))
    # 4 batch_5 waits at 4
    L4 = FleetLedger()
    for i in range(4): L4.enqueue_task(tenant_id="d", capability_id="browser.research", idempotency_key=f"b{i}", now=T0, batch_policy_id="batch_min_5", sla_policy_id="standard_2m")
    scen("batch_5 at 4", 4, 0, "batch_wait", "wait", "batch_wait" in _act(L4, "browser.research"))
    # 5 batch_5 dispatches at 5
    L4.enqueue_task(tenant_id="d", capability_id="browser.research", idempotency_key="b5", now=T0, batch_policy_id="batch_min_5", sla_policy_id="standard_2m")
    scen("batch_5 at 5", 5, 0, "batch_dispatch", "dispatch", "batch_dispatch" in _act(L4, "browser.research"))
    # 6 batch_25 dispatches at 25
    L6 = FleetLedger()
    for i in range(25): L6.enqueue_task(tenant_id="d", capability_id="verify.fact", idempotency_key=f"v{i}", now=T0, batch_policy_id="batch_min_25", sla_policy_id="standard_2m")
    scen("batch_25 at 25", 25, 0, "batch_dispatch", "dispatch", "batch_dispatch" in _act(L6, "verify.fact"))
    # 7 max_wait dispatches partial
    L7 = FleetLedger(); L7.enqueue_task(tenant_id="d", capability_id="browser.research", idempotency_key="old", now=T0, batch_policy_id="batch_min_5", sla_policy_id="standard_2m")
    scen("max_wait partial", 1, 0, "batch_dispatch", "partial", "batch_dispatch" in _act(L7, "browser.research", now="2026-06-06T00:02:00Z"))
    # 8 worker cooldown drains new task
    L8 = FleetLedger(); L8.register_worker(worker_id="wd", capability_ids=["utility.http_download"], now=T0)
    L8.enqueue_task(tenant_id="d", capability_id="utility.http_download", idempotency_key="d1", now=T0)
    L8.enqueue_task(tenant_id="d", capability_id="utility.http_download", idempotency_key="d2", now=T0)
    out = run_worker(L8, worker_id="wd", capability_id="utility.http_download", now=T0)
    scen("cooldown drain", 2, 1, "drain", "drained 2", out["processed"] == 2)
    # 9 worker exits after idle (no work)
    L9 = FleetLedger(); L9.register_worker(worker_id="we", capability_ids=["utility.http_download"], now=T0)
    out9 = run_worker(L9, worker_id="we", capability_id="utility.http_download", now=T0)
    scen("idle exit", 0, 1, "stop", "stopped", out9["processed"] == 0 and out9["status"] == "stopped")
    # 10 stale lease reclaimed
    L10 = FleetLedger(); L10.register_worker(worker_id="ws", capability_ids=["native.export"], now=T0)
    tt = L10.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="s", now=T0, batch_policy_id="on_demand_immediate")
    L10.claim_task(worker_id="ws", capability_id="native.export", now=T0, lease_seconds=10)
    scen("stale lease reclaim", 1, 1, "reclaim", "requeued", "reclaim" in _act(L10, "native.export", now="2026-06-06T00:05:00Z"))
    # 11 provider fallback
    L11 = FleetLedger(); L11.register_worker(worker_id="wf", capability_ids=["verify.fact"], now=T0)
    tf = L11.enqueue_task(tenant_id="d", capability_id="verify.fact", idempotency_key="f", now=T0, max_attempts=2, required_provider="verify.deterministic@v1", fallback_providers=["verify.llm@candidate"])
    L11.claim_task(worker_id="wf", capability_id="verify.fact", now=T0); L11.start_task(tf["task_id"], "wf", T0)
    L11.nack_task(tf["task_id"], "wf", {"e": "1"}, retryable=True, now=T0)
    provs_before = [a["provider_id"] for a in L11.attempts(tf["task_id"])]
    L11.claim_task(worker_id="wf", capability_id="verify.fact", now=T0); L11.start_task(tf["task_id"], "wf", T0)
    L11.nack_task(tf["task_id"], "wf", {"e": "2"}, retryable=True, now=T0)
    provs = [a["provider_id"] for a in L11.attempts(tf["task_id"])]
    scen("provider fallback", 1, 1, "fallback", "primary->fallback", "verify.deterministic@v1" in provs and "verify.llm@candidate" in provs and L11.task(tf["task_id"])["status"] == DEAD)
    # 12 duplicate idempotency
    L12 = FleetLedger()
    a = L12.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="dup", now=T0)
    b = L12.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="dup", now=T0)
    scen("idempotency dedup", 1, 0, "dedup", "no duplicate", a["task_id"] == b["task_id"] and len(L12.queued_tasks()) == 1)
    # 13 two workers no duplicate claim
    L13 = FleetLedger(); L13.register_worker(worker_id="a", capability_ids=["native.export"], now=T0); L13.register_worker(worker_id="b2", capability_ids=["native.export"], now=T0)
    L13.enqueue_task(tenant_id="d", capability_id="native.export", idempotency_key="x", now=T0)
    c1 = L13.claim_task(worker_id="a", capability_id="native.export", now=T0); c2 = L13.claim_task(worker_id="b2", capability_id="native.export", now=T0)
    scen("no double claim", 1, 2, "claim", "exactly one", c1 is not None and c2 is None)
    # 14 lost wakeup still processed via polling
    L14 = FleetLedger(); L14.register_worker(worker_id="lw", capability_ids=["utility.http_download"], now=T0)
    L14.enqueue_task(tenant_id="d", capability_id="utility.http_download", idempotency_key="lw", now=T0)
    out14 = run_worker(L14, worker_id="lw", capability_id="utility.http_download", now=T0)  # no wakeup signal anywhere
    scen("lost wakeup ok", 1, 1, "poll+claim", "processed", out14["processed"] == 1)

    print("SCENARIO | TASKS | WORKERS | DECISION | RESULT | STATUS")
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}")
    print(f"\n{'PASS — check_worker_fleet_supervisor_full_stack: all 14 scenarios GREEN (spawn/use-existing/SLA-spawn/batch wait+dispatch+max_wait/cooldown-drain/idle-exit/lease-reclaim/provider-fallback/idempotency/no-double-claim/lost-wakeup).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: worker fleet full stack.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
