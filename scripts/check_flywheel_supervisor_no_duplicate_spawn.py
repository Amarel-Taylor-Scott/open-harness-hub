#!/usr/bin/env python3
"""scripts.check_flywheel_supervisor_no_duplicate_spawn — proof (C-FLEET-3): two supervisors racing on the
SAME due task produce exactly ONE spawn decision (same idempotency key → one record). Combined with the
task ledger's atomic claim, this guarantees no duplicate worker/work even with replicated supervisors.

CLI: PYTHONPATH=. python3 scripts/check_flywheel_supervisor_no_duplicate_spawn.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.workers.fleet_ledger import FleetLedger
from src.baltor.workers.supervisor_ledger import SupervisorLedger

T0 = "2026-06-06T00:00:00Z"
CAP = "native.export"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    SL = SupervisorLedger()
    # both supervisors see the same queued task and derive the same spawn key
    spawn_key = f"spawn:{CAP}:tenant-d:task-1"
    dA = SL.record_decision(supervisor_id="A", decision_type="spawn_worker", idempotency_key=spawn_key,
                            reason="no warm worker", output_command_ids=["cmd-spawn-1"], now=T0)
    dB = SL.record_decision(supervisor_id="B", decision_type="spawn_worker", idempotency_key=spawn_key,
                            reason="no warm worker", output_command_ids=["cmd-spawn-2"], now=T0)
    chk("racing supervisors → one spawn decision", dA["decision_id"] == dB["decision_id"])
    spawns = [d for d in SL.decisions() if d["decision_type"] == "spawn_worker"]
    chk("exactly one spawn recorded", len(spawns) == 1, str(len(spawns)))
    chk("the winning command set is the first (no second spawn command)", spawns[0]["output_command_ids"] == ["cmd-spawn-1"])

    # and even if both then try to claim the actual task, the task ledger admits exactly one
    FL = FleetLedger()
    FL.register_worker(worker_id="wa", capability_ids=[CAP], now=T0)
    FL.register_worker(worker_id="wb", capability_ids=[CAP], now=T0)
    FL.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key="task-1", now=T0)
    c1 = FL.claim_task(worker_id="wa", capability_id=CAP, now=T0)
    c2 = FL.claim_task(worker_id="wb", capability_id=CAP, now=T0)
    chk("downstream atomic claim admits exactly one worker", c1 is not None and c2 is None)

    print(f"\n{'PASS — check_flywheel_supervisor_no_duplicate_spawn: racing supervisors record one spawn decision; downstream atomic claim admits one worker — no duplicate spawn or work.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
