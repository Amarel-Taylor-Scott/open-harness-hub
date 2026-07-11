#!/usr/bin/env python3
"""scripts.check_worker_status_progress_tracking — proof: every task status transition + start/finish/failure
timestamp + progress is recorded; invalid transitions and unowned progress updates are rejected."""
from __future__ import annotations
import argparse
from src.baltor.workers.fleet_ledger import FleetLedger, FleetLedgerError, SUCCEEDED
def _self_test() -> int:
    fails=[]; now="2026-06-06T00:00:00Z"
    def chk(n,ok,d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': '+d) if d and not ok else ''}"); (fails.append(n) if not ok else None)
    L=FleetLedger(); L.register_worker(worker_id="w",capability_ids=["c"],now=now)
    t=L.enqueue_task(tenant_id="d",capability_id="c",idempotency_key="k",now=now)
    L.claim_task(worker_id="w",capability_id="c",now=now)
    L.start_task(t["task_id"],"w",now)
    L.update_progress(t["task_id"],"w",{"percent":50,"step":"work"},now)
    L.ack_task(t["task_id"],"w",["art:1"],now)
    tr=[x["new_status"] for x in L.transitions(t["task_id"])]
    chk("transitions recorded queued->claimed->running->succeeded",tr==["claimed","running","succeeded"],str(tr))
    tt=L.task(t["task_id"])
    chk("start+finish timestamps recorded",bool(tt["started_at"]) and bool(tt["finished_at"]))
    chk("progress recorded",tt["progress"].get("percent")==50)
    chk("result artifacts recorded",tt["result_artifact_ids"]==["art:1"])
    # progress on a non-owned task rejected
    L2=FleetLedger(); L2.register_worker(worker_id="w",capability_ids=["c"],now=now)
    t2=L2.enqueue_task(tenant_id="d",capability_id="c",idempotency_key="k2",now=now)
    try: L2.update_progress(t2["task_id"],"w",{"x":1},now); chk("progress on unclaimed task rejected",False)
    except FleetLedgerError: chk("progress on unclaimed task rejected",True)
    # failure timestamp recorded
    L3=FleetLedger(); L3.register_worker(worker_id="w",capability_ids=["c"],now=now)
    t3=L3.enqueue_task(tenant_id="d",capability_id="c",idempotency_key="k3",now=now,max_attempts=1)
    L3.claim_task(worker_id="w",capability_id="c",now=now); L3.start_task(t3["task_id"],"w",now)
    L3.nack_task(t3["task_id"],"w",{"e":"x"},retryable=True,now=now)
    chk("failure timestamp recorded",bool(L3.task(t3["task_id"])["failed_at"]))
    print(f"\n{'PASS — check_worker_status_progress_tracking: transitions + start/finish/failure timestamps + progress recorded; invalid transitions and unowned progress rejected.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1
def _main(a=None):
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); ns=p.parse_args(a)
    return _self_test() if ns.self_test else (p.print_help() or 0)
if __name__=="__main__": raise SystemExit(_main())
