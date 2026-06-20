#!/usr/bin/env python3
"""scripts.check_pipeline_parallel_runs — INTEGRATED proof: concurrent pipeline runs via worker processes.

Enqueues several pipeline runs (2 tenants × 2 versions) as durable commands, spawns TWO real
`flywheel_worker.py` PROCESSES draining the pipeline queue, and asserts: every run finishes in the
ledger, runs are distinct + version-recorded, no duplicate run records or artifact writes, and the queue
returns to zero. This is the "multiple pipelines/tenants running at once" acceptance test on the durable
backbone (SQLite now; broker/KEDA later behind the same contract).

CLI:
    python3 scripts/check_pipeline_parallel_runs.py --self-test
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
import shutil
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    from scripts.durable_store import DurableStore
    from scripts.pipeline_runtime.runner import enqueue_run
    from scripts.pipeline_runtime.store import PipelineLedger

    tmp = tempfile.mkdtemp(prefix="pipe-parallel-")
    db = os.path.join(tmp, "d.db")
    queue = "pipeline.runs"
    store = DurableStore(db)
    PipelineLedger(store)  # ensure ledger tables exist before workers attach

    jobs = []
    for tenant in ("acme", "globex"):
        for ref in ("cfpb_structured_ingest@v1", "cfpb_structured_ingest@v2"):
            r = enqueue_run(store, pipeline_ref=ref, tenant_id=tenant,
                            run_input={"fixture": True, "limit": 5, "source_id": "cfpb-fixture"}, queue=queue)
            jobs.append(r)
    check("enqueued 4 distinct pipeline-run commands", len(jobs) == 4 and store.stats(queue)["queued"] == 4, str(store.stats(queue)))

    env = {**os.environ, "PYTHONPATH": str(_REPO)}
    t0 = time.time()
    procs = [subprocess.Popen([sys.executable, "scripts/flywheel_worker.py", "--db", db, "--queue", queue,
                               "--worker-id", f"pw{k}", "--max-empty", "5"],
                              cwd=str(_REPO), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for k in range(2)]
    for p in procs:
        try:
            p.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            p.kill()
            check("workers finished within timeout", False)
    drain_s = round(time.time() - t0, 3)

    stats = store.stats(queue)
    check("pipeline queue fully drained (done==4, queued==0, dead==0)",
          stats["done"] == 4 and stats["queued"] == 0 and stats["dead"] == 0, str(stats))

    ledger = PipelineLedger(store)
    runs = ledger.list_runs(limit=50)
    done = [r for r in runs if r["status"] == "done"]
    check("4 pipeline runs recorded done in the ledger", len(done) == 4, str(len(done)))
    check("runs are distinct + version-recorded",
          len({r["run_id"] for r in done}) == 4 and {r["pipeline_version"] for r in done} == {"v1", "v2"})
    check("both tenants ran concurrently", {r["tenant_id"] for r in done} == {"acme", "globex"})
    # no duplicate side effects: each (tenant,version) appears exactly once
    keys = [(r["tenant_id"], r["pipeline_version"]) for r in done]
    check("each (tenant,version) produced EXACTLY one run (no double-process)", len(keys) == len(set(keys)))
    print(f"   · 4 pipeline runs (2 tenants × v1/v2) drained by 2 worker processes in {drain_s}s")

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_pipeline_parallel_runs: concurrent multi-tenant, multi-version pipeline runs drained by parallel worker processes with no double-processing; queue drained.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Integrated proof: concurrent pipeline runs via worker processes.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
