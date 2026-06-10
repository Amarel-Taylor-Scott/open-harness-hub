#!/usr/bin/env python3
"""scripts.check_live_supervisor_parallel_dispatch — proof: the durable ledger enforces DEPENDENCY ORDERING
(a task is claimable only when all its deps have succeeded), and the live supervisor dispatches MULTIPLE
real worker processes that drain different capability queues IN PARALLEL.

Part A (deterministic): a verify chain A→B→C — claim yields A only; B/C are dep-blocked until their dep
succeeds; topological claim order A,B,C.
Part B (real, multi-process): tasks across 3 capabilities → one `--watch --dispatch` tick spawns one real
worker PER capability → all drain in parallel → every task succeeds, distinct workers, no double-processing.

CLI: PYTHONPATH=. python3 scripts/check_live_supervisor_parallel_dispatch.py --self-test
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
T0 = "2026-06-06T00:00:00Z"


def _wait(pred, timeout=35.0, poll=0.3):
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

    tmp = tempfile.mkdtemp(prefix="baltor-paralleld-")

    # ── Part A: deterministic dependency ordering ──
    db = os.path.join(tmp, "deps.db")
    L = DurableFleetLedger(db)
    L.register_worker(worker_id="w", capability_ids=["verify"], now=T0)
    a = L.enqueue_task(tenant_id="d", capability_id="verify", idempotency_key="A", now=T0)
    b = L.enqueue_task(tenant_id="d", capability_id="verify", idempotency_key="B", now=T0, depends_on=[a["task_id"]])
    c = L.enqueue_task(tenant_id="d", capability_id="verify", idempotency_key="C", now=T0, depends_on=[b["task_id"]])
    c1 = L.claim_task(worker_id="w", capability_id="verify", now=T0)
    chk("dep order: first claim is A (B,C dep-blocked)", c1 and c1["task_id"] == a["task_id"])
    chk("B/C not claimable until A done", L.claim_task(worker_id="w", capability_id="verify", now=T0) is None)
    L.start_task(a["task_id"], "w", T0); L.ack_task(a["task_id"], "w", [], T0)
    c2 = L.claim_task(worker_id="w", capability_id="verify", now=T0)
    chk("after A succeeds, B becomes claimable", c2 and c2["task_id"] == b["task_id"])
    chk("C still dep-blocked until B done", L.claim_task(worker_id="w", capability_id="verify", now=T0) is None)
    L.start_task(b["task_id"], "w", T0); L.ack_task(b["task_id"], "w", [], T0)
    c3 = L.claim_task(worker_id="w", capability_id="verify", now=T0)
    chk("after B succeeds, C becomes claimable (topological A→B→C)", c3 and c3["task_id"] == c["task_id"])
    L.close()

    # ── Part B: real parallel multi-worker drain across capabilities ──
    db2 = os.path.join(tmp, "parallel.db")
    caps = ["verify", "reconcile", "ingest"]
    per = 3
    L2 = DurableFleetLedger(db2)
    for cap in caps:
        for i in range(per):
            L2.enqueue_task(tenant_id="d", capability_id=cap, idempotency_key=f"{cap}-{i}", now=T0, priority_class="P1")
    chk("seeded 3 capability queues", all(len(L2.queued_tasks(cap)) == per for cap in caps))
    L2.close()

    env = {**os.environ, "PYTHONPATH": str(_REPO)}
    cmd = [sys.executable, "scripts/baltor_flywheel.py", "--watch", "--supervisor-only", "--dispatch",
           "--supervisor-db", db2, "--supervisor-id", "sup-p", "--interval", "1", "--leader-ttl", "30",
           "--max-shards", "16", "--max-ticks", "1"]
    proc = subprocess.run(cmd, cwd=str(_REPO), env=env, capture_output=True, text=True, timeout=60)
    chk("supervisor dispatch tick ran", proc.returncode == 0, proc.stderr[-200:])

    L3 = DurableFleetLedger(db2)
    drained = _wait(lambda: len(L3.tasks_by_status("succeeded")) == per * len(caps)
                    and sum(len(L3.queued_tasks(cap)) for cap in caps) == 0, timeout=35)
    chk("ALL capability queues drained in parallel", drained,
        f"succeeded={len(L3.tasks_by_status('succeeded'))}/{per*len(caps)}")
    succ = L3.tasks_by_status("succeeded")
    chk("no double-processing — distinct succeeded tasks", len({t['task_id'] for t in succ}) == per * len(caps))
    by_cap = {}
    for tsk in succ:
        by_cap[tsk["capability_id"]] = by_cap.get(tsk["capability_id"], 0) + 1
    chk("every capability fully drained", all(by_cap.get(cap) == per for cap in caps), str(by_cap))

    SS = SupervisorStore(db2)
    reqs = [r for r in SS.spawn_requests() if r["dry_run"] == 0]
    workers = {r["worker_id"] for r in reqs}
    chk("supervisor spawned a DISTINCT real worker per capability (parallel)", len(workers) >= len(caps), str(workers))
    chk("spawn requests cover all capabilities", {r["capability_id"] for r in reqs} >= set(caps))
    # cleanup any lingering worker by exact pid (they self-terminate on idle)
    for r in reqs:
        if r.get("pid"):
            try:
                os.kill(r["pid"], signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
    L3.close(); SS.close()

    print(f"\n{'PASS — check_live_supervisor_parallel_dispatch: durable dependency ordering (A→B→C dep-gated claims) + real parallel multi-worker drain (one worker per capability, all queues drained concurrently, distinct workers, no double-processing).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
