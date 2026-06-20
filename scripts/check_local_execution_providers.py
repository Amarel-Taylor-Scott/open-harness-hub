#!/usr/bin/env python3
"""scripts.check_local_execution_providers — proof: the LOCAL execution equivalents are real, working
offline providers (no Docker/cloud/global-pip/sudo). managed_venv runs a bounded local task + enforces
timeout; local_job_emulator drains a batch (full + partial); local_worker_pool splits across N workers with
no double-processing; container_image_emulator falls back to managed_venv when Docker is absent. None
publish truth. This is the capability that must exist BEFORE any cloud item may be deferred.

CLI: PYTHONPATH=. python3 scripts/check_local_execution_providers.py --self-test
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
from src.baltor.workers.execution_providers.container_image_emulator import ContainerImageEmulator
from src.baltor.workers.execution_providers.local_job_emulator import LocalCloudRunJobEmulator, LocalJobEmulator
from src.baltor.workers.execution_providers.local_worker_pool import LocalWorkerPool
from src.baltor.workers.execution_providers.managed_venv import ManagedVenvProvider

_REPO = Path(__file__).resolve().parents[1]
CAP = "utility.hash"


def _seed(db, n):
    L = DurableFleetLedger(db)
    for i in range(n):
        L.enqueue_task(tenant_id="t", capability_id=CAP, idempotency_key=f"k{i}")
    L.close()


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-localexec-")

    # managed venv: runs a real local task, enforces timeout, no global pip/sudo/docker, no truth
    mv = ManagedVenvProvider()
    r = mv.run_python(cache_key="k1", code="print(40+2)", task_id="t1")
    chk("managed_venv runs a local task", r.status == "succeeded" and "42" in r.detail.get("stdout", ""))
    chk("managed_venv created a venv cache dir", (_REPO / ".agent" / "venvs" / "k1").exists())
    chk("managed_venv enforces timeout (structured failure, no hang)",
        mv.run_python(cache_key="k1", code="import time;time.sleep(5)", task_id="t2", timeout_s=1).status == "failed")
    chk("managed_venv publishes no truth", r.is_truth is False)
    mv_src = (_REPO / "src/teleon/runtime/execution_providers/managed_venv.py").read_text()  # canonical Teleon home (Baltor re-exports)
    # match actual call-forms, not the prohibition words in the docstring
    chk("managed_venv invokes NO global pip/sudo/apt/docker (call-forms)",
        not any(t in mv_src for t in ('"sudo"', '"docker"', '"apt-get"', '"brew"', "pip install", "os.system(", "apt install")))

    # local job emulator: batch full + partial
    db = os.path.join(tmp, "j.db"); _seed(db, 7)
    j = LocalJobEmulator().invoke_batch(db, capability=CAP, batch_min=5)
    chk("local_job_emulator drains a full batch of 5", j["processed"] == 5 and j["partial"] is False)
    jp = LocalJobEmulator().invoke_batch(db, capability=CAP, batch_min=5)  # only 2 left → partial
    chk("local_job_emulator dispatches a PARTIAL batch when fewer remain", jp["processed"] == 2 and jp["partial"] is True)
    chk("cloud-run-job alias exists", LocalCloudRunJobEmulator().provider_id == "execution.local_cloud_run_job_emulator@v1")

    # local worker pool: split across 2 workers, no double-processing
    db2 = os.path.join(tmp, "p.db"); _seed(db2, 6)
    pool = LocalWorkerPool().run_pool(db2, capability=CAP, n_workers=2)
    chk("local_worker_pool total == queue (no double-processing)", pool["total_processed"] == 6)
    chk("local_worker_pool split across 2 workers", len(pool["per_worker"]) == 2)
    L3 = DurableFleetLedger(db2)
    chk("exactly 6 succeeded durably", len(L3.tasks_by_status("succeeded")) == 6)
    L3.close()

    # container image emulator: Docker unavailable → managed_venv fallback (not blocked), same contract
    ci = ContainerImageEmulator(docker_available=False).run(image="py:demo", command=[sys.executable, "-c", "print(1)"], task_id="c1")
    chk("container task runs via managed_venv when Docker absent (not blocked)", ci["status"] == "succeeded" and ci["backend_used"] == "managed_venv_fallback")
    chk("container emulator publishes no truth", ci["is_truth"] is False)

    print(f"\n{'PASS — check_local_execution_providers: managed_venv + local_job + local_worker_pool + container fallback are real working offline providers (timeout, batch+partial, no-double-claim, Docker-absent fallback, no global pip, no truth).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
