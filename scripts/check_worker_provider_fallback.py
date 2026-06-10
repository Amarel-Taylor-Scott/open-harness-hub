#!/usr/bin/env python3
"""scripts.check_worker_provider_fallback — proof: a failing task retries the primary provider then FALLS
BACK to the next provider in fallback_order, without duplicating the task; final failure goes dead/DLQ."""
from __future__ import annotations
import argparse
from src.baltor.workers.fleet_ledger import FleetLedger, DEAD
def _self_test() -> int:
    fails=[]; now="2026-06-06T00:00:00Z"
    def chk(n,ok,d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': '+d) if d and not ok else ''}"); (fails.append(n) if not ok else None)
    L=FleetLedger(); L.register_worker(worker_id="w",capability_ids=["verify.fact"],now=now)
    t=L.enqueue_task(tenant_id="d",capability_id="verify.fact",idempotency_key="k",now=now,max_attempts=2,
                     required_provider="verify.deterministic@v1",fallback_providers=["verify.llm@candidate"])
    # attempt 0 — primary
    L.claim_task(worker_id="w",capability_id="verify.fact",now=now); L.start_task(t["task_id"],"w",now)
    L.nack_task(t["task_id"],"w",{"e":"1"},retryable=True,now=now)
    # attempt 1 — fallback provider
    L.claim_task(worker_id="w",capability_id="verify.fact",now=now); L.start_task(t["task_id"],"w",now)
    L.nack_task(t["task_id"],"w",{"e":"2"},retryable=True,now=now)
    provs=[a["provider_id"] for a in L.attempts(t["task_id"])]
    chk("primary provider used first",provs and provs[0]=="verify.deterministic@v1",str(provs))
    chk("fallback provider used after primary failure budget","verify.llm@candidate" in provs,str(provs))
    chk("task NOT duplicated (single task row)",len(L.queued_tasks())+len(L.tasks_by_status(DEAD))==1)
    chk("final failure → dead/DLQ",L.task(t["task_id"])["status"]==DEAD)
    print(f"\n{'PASS — check_worker_provider_fallback: primary→fallback provider progression, single task (no duplicate side effect), final failure dead.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1
def _main(a=None):
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); ns=p.parse_args(a)
    return _self_test() if ns.self_test else (p.print_help() or 0)
if __name__=="__main__": raise SystemExit(_main())
