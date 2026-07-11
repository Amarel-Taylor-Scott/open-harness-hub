#!/usr/bin/env python3
"""scripts.check_live_supervisor_spawn_decisions — proof (OPP-supervisor-scaling-live): the LIVE supervisor
tick CALLS spawn-decision logic over its owned capability shards and records an IDEMPOTENT spawn decision
when queued work needs a worker — and records NOTHING when a warm worker already meets SLA. It DECIDES +
RECORDS only; it never executes the task (no heavy work inside the supervisor).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_spawn_decisions.py --self-test
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from src.baltor.workers import supervisor_watch
from src.baltor.workers.fleet_ledger import FleetLedger
from src.baltor.workers.supervisor_store import SupervisorStore

ISO = "2026-06-06T00:00:00Z"
CAP = "verify"   # a capability shard id the supervisor owns


def _fresh_store(tmp, name):
    s = SupervisorStore(Path(tmp) / name)
    s.register_instance(supervisor_id="A", now=1000)
    return s


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-spawn-")

    # 1 — on-demand task + NO worker → the live tick records a spawn decision
    s = _fresh_store(tmp, "a.db")
    fl = FleetLedger()
    fl.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="q1", now=ISO, priority_class="P1")
    out = supervisor_watch.step(s, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16,
                                now=1000, iso_now=ISO, fleet_ledger=fl)
    chk("supervisor owns the capability shard", CAP in out["owned_shards"])
    spawns = s.spawn_decisions()
    chk("on-demand + no worker → spawn decision recorded by the live tick", len(spawns) == 1, str(len(spawns)))
    chk("spawn decision names the capability + action", spawns and spawns[0]["capability_id"] == CAP and spawns[0]["action"] == "spawn_new_worker")
    chk("no heavy execution — task still QUEUED (supervisor did not process it)", fl.task(fl.queued_tasks(CAP)[0]["task_id"] if fl.queued_tasks(CAP) else "x") is not None and len(fl.queued_tasks(CAP)) == 1)

    # 2 — idempotent: a second identical tick over the same queued task records NO new spawn decision
    supervisor_watch.step(s, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16,
                          now=1001, iso_now=ISO, fleet_ledger=fl)
    chk("duplicate spawn decision prevented (idempotent across ticks)", len(s.spawn_decisions()) == 1, str(len(s.spawn_decisions())))

    # 3 — warm worker that meets SLA → NO spawn decision
    s2 = _fresh_store(tmp, "b.db")
    fl2 = FleetLedger()
    fl2.register_worker(worker_id="w", capability_ids=[CAP], max_concurrency=4, now=ISO)
    fl2.set_worker_status("w", "warm", now=ISO)
    fl2.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="q2", now=ISO, priority_class="P1")
    supervisor_watch.step(s2, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16,
                          now=1000, iso_now=ISO, fleet_ledger=fl2)
    chk("warm worker meets SLA → no spawn decision", len(s2.spawn_decisions()) == 0, str(len(s2.spawn_decisions())))

    # 4 — no queued work → no spawn decision (the call still happens; it is a safe no-op)
    s3 = _fresh_store(tmp, "c.db")
    supervisor_watch.step(s3, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16,
                          now=1000, iso_now=ISO, fleet_ledger=FleetLedger())
    chk("no queued work → no spawn decision", len(s3.spawn_decisions()) == 0)

    # 5 — the bare watch loop (no fleet_ledger) calls the pass safely (no-op, no crash)
    s4 = _fresh_store(tmp, "d.db")
    out4 = supervisor_watch.step(s4, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16, now=1000, iso_now=ISO)
    chk("bare watch tick runs spawn pass safely (no ledger → no-op)", out4["tick_id"] and len(s4.spawn_decisions()) == 0)

    # 6 — determinism
    sA = _fresh_store(tmp, "e1.db"); flA = FleetLedger(); flA.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="z", now=ISO, priority_class="P1")
    supervisor_watch.step(sA, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16, now=1000, iso_now=ISO, fleet_ledger=flA)
    sB = _fresh_store(tmp, "e2.db"); flB = FleetLedger(); flB.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="z", now=ISO, priority_class="P1")
    supervisor_watch.step(sB, supervisor_id="A", leader_ttl=300, shard_ttl=300, max_shards=16, now=1000, iso_now=ISO, fleet_ledger=flB)
    chk("deterministic spawn decision id", sA.spawn_decisions()[0]["idempotency_key"] == sB.spawn_decisions()[0]["idempotency_key"])

    print(f"\n{'PASS — check_live_supervisor_spawn_decisions: live tick CALLS spawn-decision over owned shards; spawn recorded when work needs a worker, none when SLA met; idempotent; no heavy execution; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
