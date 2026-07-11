#!/usr/bin/env python3
"""scripts.check_worker_fleet_redteam — adversarial proof: fleet-scheduler attacks fail safely."""
from __future__ import annotations
import argparse
from pathlib import Path
from src.baltor.workers.fleet_ledger import FleetLedger, FleetLedgerError, SUCCEEDED
from src.baltor.workers.fleet_supervisor import decide_for_capability
from src.baltor.workers import local_spawn_manager as sm
def _self_test() -> int:
    fails=[]; now="2026-06-06T00:00:00Z"
    def chk(n,blocked,d=""):
        print(f"  [{'ok' if blocked else 'FAIL'}] BLOCKED: {n}{(': '+d) if d and not blocked else ''}"); (fails.append(n) if not blocked else None)
    L=FleetLedger(); L.register_worker(worker_id="a",capability_ids=["utility.http_download"],now=now); L.register_worker(worker_id="b",capability_ids=["utility.http_download"],now=now)
    t=L.enqueue_task(tenant_id="d",capability_id="utility.http_download",idempotency_key="k",now=now)
    L.claim_task(worker_id="a",capability_id="utility.http_download",now=now)
    chk("two workers claim same task", L.claim_task(worker_id="b",capability_id="utility.http_download",now=now) is None)
    # process without claim (start a task you don't own)
    L2=FleetLedger(); L2.register_worker(worker_id="x",capability_ids=["utility.http_download"],now=now)
    t2=L2.enqueue_task(tenant_id="d",capability_id="utility.http_download",idempotency_key="k2",now=now)
    try: L2.start_task(t2["task_id"],"x",now); chk("process task without atomic claim",False)
    except FleetLedgerError: chk("process task without atomic claim",True)
    # status jump queued->succeeded
    try: L2._transition(t2["task_id"],SUCCEEDED,now=now); chk("status jump queued->succeeded",False)
    except FleetLedgerError: chk("status jump queued->succeeded",True)
    # unknown capability spawns worker
    L3=FleetLedger(); L3.enqueue_task(tenant_id="d",capability_id="totally.unknown",idempotency_key="u",now=now)
    d=decide_for_capability(L3,"totally.unknown",now=now)
    chk("unknown capability spawns worker", all(x["action"]!="spawn" for x in d) and any(x["action"]=="reject" for x in d), str([x['action'] for x in d]))
    # worker claims outside its allowed capability
    L4=FleetLedger(); L4.register_worker(worker_id="w",capability_ids=["utility.http_download"],now=now)
    L4.enqueue_task(tenant_id="d",capability_id="verify.fact",idempotency_key="vf",now=now)
    try: L4.claim_task(worker_id="w",capability_id="verify.fact",now=now); chk("worker claims task outside allowed capability",False)
    except FleetLedgerError: chk("worker claims task outside allowed capability",True)
    # stale worker keeps lease forever -> reclaim
    L5=FleetLedger(); L5.register_worker(worker_id="s",capability_ids=["utility.http_download"],now=now)
    ts=L5.enqueue_task(tenant_id="d",capability_id="utility.http_download",idempotency_key="s",now=now)
    L5.claim_task(worker_id="s",capability_id="utility.http_download",now=now,lease_seconds=10)
    chk("stale worker keeps lease forever", ts["task_id"] in L5.reclaim_expired_leases("2026-06-06T01:00:00Z"))
    # lost wakeup -> task still processed via polling/claim (no signal needed)
    L6=FleetLedger(); L6.register_worker(worker_id="p",capability_ids=["utility.http_download"],now=now)
    L6.enqueue_task(tenant_id="d",capability_id="utility.http_download",idempotency_key="p",now=now)
    claimed=L6.claim_task(worker_id="p",capability_id="utility.http_download",now=now)  # no wakeup signal at all
    chk("task lost if wakeup signal lost", claimed is not None)
    # broad pkill used
    chk("broad pkill used in spawn manager", "pkill" not in Path(sm.__file__).read_text() and "killall" not in Path(sm.__file__).read_text())
    print(f"\n{'PASS — check_worker_fleet_redteam: duplicate claim, claim-less processing, status jumps, unknown-capability spawn, cross-capability claim, eternal lease, lost-wakeup loss, and pkill all fail safely.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1
def _main(a=None):
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); ns=p.parse_args(a)
    return _self_test() if ns.self_test else (p.print_help() or 0)
if __name__=="__main__": raise SystemExit(_main())
