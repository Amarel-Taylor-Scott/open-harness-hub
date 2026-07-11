#!/usr/bin/env python3
"""scripts.check_control_plane_tick — proof (C-FLEET-3 glue): one composed control-plane tick acquires the
leader lease, scans its owned capability shard in the DB task ledger, consults the spawn-decision engine,
records an IDEMPOTENT spawn decision, and records the tick for lag accounting. Two supervisors over the
same shard produce NO duplicate spawn (leader lease + idempotent decision). It only decides — workers
still claim atomically.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_control_plane_tick.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.control_plane import control_plane_tick
from src.baltor.workers.fleet_ledger import FleetLedger
from src.baltor.workers.supervisor_ledger import SupervisorLedger
from src.baltor.workers.supervisor_metrics import lag_metrics

T0 = "2026-06-06T00:00:00Z"
CAP = "native.export"   # real capability in worker_capability_registry.json (on_demand, interactive)


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    FL = FleetLedger()
    FL.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="t1", now=T0, priority_class="P1")
    SL = SupervisorLedger()
    SL.register_instance(supervisor_id="A", now=T0)

    # leader tick: queued work + no worker → spawn decision recorded
    out = control_plane_tick(supervisor_ledger=SL, fleet_ledger=FL, supervisor_id="A", now=T0, owned_shards=[CAP])
    chk("tick acquires leader lease", out["is_leader"] is True)
    chk("tick counts due work", out["due_task_count"] == 1)
    chk("tick records a spawn decision (no worker for queued task)", len(out["decisions"]) == 1, str(out["decisions"]))
    chk("a tick was recorded for lag accounting", len(SL.ticks()) == 1)
    chk("tick decided only — no worker spawned/executed", FL.tasks_by_status("running") == [])

    # second supervisor, same shard, same now → leader lease denied, decision idempotent (no dup spawn)
    SL.register_instance(supervisor_id="B", now=T0)
    out2 = control_plane_tick(supervisor_ledger=SL, fleet_ledger=FL, supervisor_id="B", now=T0, owned_shards=[CAP])
    chk("second supervisor is not leader (lease held)", out2["is_leader"] is False)
    spawns = [d for d in SL.decisions() if d["decision_type"] == "spawn_worker"]
    chk("no duplicate spawn across two supervisors", len(spawns) == 1, str(len(spawns)))

    # idle shard: no queued work → no decision, still records a tick
    FL2 = FleetLedger(); SL2 = SupervisorLedger(); SL2.register_instance(supervisor_id="A", now=T0)
    out3 = control_plane_tick(supervisor_ledger=SL2, fleet_ledger=FL2, supervisor_id="A", now=T0, owned_shards=[CAP])
    chk("idle shard → no decisions", out3["decisions"] == [] and out3["due_task_count"] == 0)
    chk("idle tick still recorded", len(SL2.ticks()) == 1)

    # lag metrics computed from the recorded ticks
    m = lag_metrics(SL, now=T0)
    chk("lag metrics see the ticks", m["tick_count"] == 2)

    # determinism: same setup → same decision id
    def run():
        fl = FleetLedger(); fl.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="t1", now=T0, priority_class="P1")
        sl = SupervisorLedger(); sl.register_instance(supervisor_id="A", now=T0)
        return control_plane_tick(supervisor_ledger=sl, fleet_ledger=fl, supervisor_id="A", now=T0, owned_shards=[CAP])["decisions"][0]["decision_id"]
    chk("deterministic decision id", run() == run())

    print(f"\n{'PASS — check_control_plane_tick: composed tick = leader lease + queue scan + spawn_decision + idempotent decision + lag tick; no duplicate spawn across supervisors; decides only; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
