#!/usr/bin/env python3
"""scripts.check_pipeline_per_step_queue — proof: a pipeline run completes ACROSS per-step queues.

Proves the per-step routing model (vs inline): starting a run enqueues only its first ready step; nothing
executes until a worker drains that step's queue; completing a step ENQUEUES the next dependent step on
ITS queue; draining all step queues completes the run. Each step is processed exactly once and the run's
artifacts/gates land — proving steps flow step→queue→worker→next-step, not inline.

CLI:
    python3 scripts/check_pipeline_per_step_queue.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile

from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.processors import default_registry
from scripts.pipeline_runtime.runner import drain_steps, run_step_command, start_run_via_queue, step_queues
from scripts.pipeline_runtime.specs import discover
from scripts.pipeline_runtime.store import PipelineLedger


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="pipe-perstep-")
    store = DurableStore(tmp + "/d.db")
    ledger = PipelineLedger(store)
    reg = default_registry()
    spec = discover()["cfpb_structured_ingest@v1"]
    queues = step_queues(spec)
    run_input = {"fixture": True, "limit": 5, "source_id": "cfpb"}

    start = start_run_via_queue(store, ledger, spec, tenant_id="acme", run_input=run_input)
    run_id = start["run_id"]
    check("starting a run enqueues ONLY the first ready step (source)", start["enqueued_steps"] == ["source"], str(start["enqueued_steps"]))
    check("run is NOT done yet (nothing executed inline)", ledger.get_run(run_id)["status"] == "running")
    check("only the source queue has work; downstream queues empty",
          store.stats(queues[0])["queued"] == 1 and all(store.stats(q)["queued"] == 0 for q in queues[1:]))

    # drain JUST the source step → it must enqueue the next step (decompose) on the next queue
    job = store.claim(queues[0], worker="w", lease_seconds=60, now=1)
    res = run_step_command(store, ledger, reg, job["payload"])
    store.ack(job["id"])
    check("source step completes via the queue", res["status"] == "done" and res["step"] == "source")
    check("completing source ENQUEUED the next step (decompose) on its queue",
          store.stats(queues[1])["queued"] == 1 and "decompose" in res["enqueued_next"], str(store.stats(queues[1])))
    check("source queue now drained (1 done)", store.stats(queues[0])["done"] == 1 and store.stats(queues[0])["queued"] == 0)

    # drain the remaining step queues to completion
    processed = drain_steps(store, ledger, reg, queues=queues, now=2)
    rec = ledger.get_run(run_id)
    check("run reaches done across all step queues", rec["status"] == "done", str(rec["status"]))
    check("all 4 steps recorded done", len(rec["steps"]) == 4 and all(s["status"] == "done" for s in rec["steps"]))
    steps_seen = [p[1] for p in processed] + ["source"]
    check("each step executed exactly once (no double-process)", sorted(set(steps_seen)) == ["decompose", "govern", "package", "source"] and len(steps_seen) == len(set(steps_seen)))
    arts = ledger.run_artifacts(run_id)
    check("terminal ContextPack artifact produced", "ContextPack.v1" in arts and arts["ContextPack.v1"].get("context_pack_id"))
    check("receipt facts_served matches verified facts (gate held across queues)",
          arts["Receipt.v1"]["facts_served"] == arts["VerifiedFactSet.v1"]["count"])
    check("all step queues fully drained", all(store.stats(q)["queued"] == 0 and store.stats(q)["dead"] == 0 for q in queues))

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_pipeline_per_step_queue: a run flows step→queue→worker→next-step across per-step lanes (not inline); each step once; run completes with gates + content-addressed artifacts.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline run completes across per-step queues.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
