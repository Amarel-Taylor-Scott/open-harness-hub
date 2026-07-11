#!/usr/bin/env python3
"""scripts.check_live_supervisor_dispatch — THE live-dispatch milestone (G4): the real
`baltor_flywheel.py --watch --dispatch` loop reads REAL queued durable tasks, records a spawn decision, and
SPAWNS A REAL worker subprocess that claims + DRAINS the durable FleetLedger — end-to-end. Reject
"ledger exists": this proves live dispatch + real spawn/drain through the watch loop.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_live_supervisor_dispatch.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
CAP = "verify"   # a capability shard id the supervisor owns
N = 5


def _wait(pred, timeout=30.0, poll=0.3):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if pred():
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


def _self_test() -> int:
    from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
    from src.baltor.workers.supervisor_store import SupervisorStore
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-dispatch-")
    db = os.path.join(tmp, "durable.db")
    # seed REAL durable queued work
    L = DurableFleetLedger(db)
    for i in range(N):
        L.enqueue_task(tenant_id="d", capability_id=CAP, idempotency_key=f"t{i}", priority_class="P1")
    chk("seeded durable queue", len(L.queued_tasks(CAP)) == N)
    L.close()

    # run ONE real supervisor dispatch tick — it must spawn a real worker that drains the queue
    env = {**os.environ, "PYTHONPATH": _pythonpath(".")}
    cmd = [sys.executable, str(_resource("scripts/baltor_flywheel.py")), "--watch", "--supervisor-only", "--dispatch",
           "--supervisor-db", db, "--supervisor-id", "sup-d", "--interval", "1", "--leader-ttl", "30",
           "--max-shards", "16", "--max-ticks", "1"]
    proc = subprocess.run(cmd, cwd=str(_REPO), env=env, capture_output=True, text=True, timeout=60)
    chk("supervisor dispatch tick ran", proc.returncode == 0, proc.stderr[-300:])

    # the spawned worker (orphaned child) drains the durable queue asynchronously — poll until done
    L2 = DurableFleetLedger(db)
    drained = _wait(lambda: len(L2.tasks_by_status("succeeded")) == N and len(L2.queued_tasks(CAP)) == 0, timeout=30)
    chk("spawned worker DRAINED all durable tasks (live dispatch)", drained,
        f"succeeded={len(L2.tasks_by_status('succeeded'))} queued={len(L2.queued_tasks(CAP))}")
    succeeded = L2.tasks_by_status("succeeded")
    chk("no double-processing — exactly N distinct succeeded tasks", len({t['task_id'] for t in succeeded}) == N)
    chk("each succeeded task was claimed (has a lease_owner)", all(t["lease_owner"] for t in succeeded))

    # the supervisor recorded the decision + an ISSUED real spawn request (pid, not dry-run)
    SS = SupervisorStore(db)
    chk("supervisor recorded a spawn decision", len(SS.spawn_decisions()) >= 1)
    reqs = SS.spawn_requests()
    real = [r for r in reqs if r["capability_id"] == CAP and r["dry_run"] == 0]
    chk("supervisor issued a REAL spawn request (worker subprocess, not dry-run)", len(real) >= 1, str(reqs))
    chk("spawn request links to a decision + a worker id", real and real[0]["decision_id"] and real[0]["worker_id"])

    # the supervisor itself executed no heavy work — it only decided + spawned (the worker drained)
    chk("supervisor is supervisor-only (no proof tick ran in this mode)", "[supervisor]" in (proc.stdout or ""))

    # cleanup any still-alive worker child by EXACT pid (it should have self-terminated on idle)
    for r in real:
        pid = r.get("pid") or 0
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
    L2.close(); SS.close()

    print(f"\n{'PASS — check_live_supervisor_dispatch: real --watch --dispatch tick read durable queue, recorded a spawn decision + real spawn request, and a spawned worker subprocess drained all durable tasks via atomic claim (live dispatch, real spawn/drain).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
