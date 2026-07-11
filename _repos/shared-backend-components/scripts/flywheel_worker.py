#!/usr/bin/env python3
"""scripts.flywheel_worker — a STANDALONE durable worker process (the real push/pull execution).

The piece that turns the durable queue into a fleet: a stateless claim-loop process that pulls jobs
from a durable queue (lease), runs a handler, and ack/nacks — with backoff when idle and exit after K
empty polls. Run N of these against one queue and they share the work with **no double-processing**
(SQLite `BEGIN IMMEDIATE` + busy_timeout serialize claims across PROCESSES). This is exactly the shape a
KEDA-scaled K8s Deployment replaces later — same claim/ack/lease/DLQ contract (`durable_store`).

Handler contract: ``handler(store, job) -> None`` (raise to nack→retry→DLQ). The default handler is
idempotent: it records the job's ``doc_id`` once (so a double-process would be detectable) and emits a
durable Work-plane event; tenant-ingest payloads are decomposed into atomic facts.

CLI:
    python3 _repos/shared-backend-components/scripts/flywheel_worker.py --db .agent/durable.db --queue ingest.acme --worker-id w1
    python3 _repos/shared-backend-components/scripts/flywheel_worker.py --self-test
"""
from __future__ import annotations

import argparse
import time
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.durable_store import DurableStore

DEFAULT_LEASE_S = 30
DEFAULT_MAX_EMPTY = 3        # exit after this many consecutive empty polls (so a drain terminates)
DEFAULT_IDLE_S = 0.02
EPOCH_CONSUME = "1970-01-01T00:00:00Z"  # injected clock for durable context.consume (deterministic, no wall-clock)


class PermanentJobError(Exception):
    """A job that can never succeed (e.g. a schema-invalid CommandEnvelope). Dead-letters immediately —
    retrying it would only burn the retry budget reprocessing a command that cannot pass validation."""


def default_handler(store: DurableStore, job: dict) -> dict[str, Any]:
    """Idempotent default, routed by command_type: a `pipeline.run` command runs a versioned pipeline via
    the Pipeline Runtime; otherwise a tenant/doc job is decomposed into atomic facts. Both emit a durable
    Work-plane event + use an idempotency guard."""
    p = job.get("payload") or {}
    if p.get("command_type") == "pipeline.run_step":
        # C32 contract layer: a CommandEnvelope routed through the standard ProcessorHarness (registry only).
        from scripts.runtime.context import build_context
        from scripts.runtime.processor_harness import run_command
        from scripts.runtime.processor_registry import default_registry as rt_registry

        class _DurableBus:  # publish EventEnvelopes onto the ONE durable event log (no second bus)
            def publish_event(self, ev) -> None:
                d = ev.to_dict() if hasattr(ev, "to_dict") else ev
                store.append_event({"seq": None, "kind": d.get("type", "event"), "stage": "Work plane",
                                    "component": "runtime_harness", "correlation_id": d.get("correlation_id"),
                                    "object_ref": d.get("run_id"), "payload": d.get("data", {})})

        ctx = build_context(tenant_id=p.get("tenant_id", ""), run_id=p.get("run_id", ""),
                            pipeline_id=p.get("pipeline_id", ""), pipeline_version=p.get("pipeline_version", ""),
                            step_id=p.get("step_id", ""), durable_store=store, event_bus=_DurableBus())
        out = run_command(rt_registry(), p, ctx)
        store.append_event({"seq": None, "kind": "pipeline.step.completed" if out["ok"] else "processor.failed",
                            "stage": "Work plane", "component": "runtime_harness", "correlation_id": p.get("tenant_id"),
                            "object_ref": p.get("run_id"), "payload": ({"step_id": p.get("step_id")} if out["ok"] else out["error"])})
        if not out["ok"]:
            # ack/nack depends on the harness verdict: retryable → nack→retry→DLQ; permanent (e.g. schema
            # validation failure) → immediate DLQ (never reprocessed). The processor.failed event above is
            # already recorded durably either way.
            msg = f"{'retryable' if out['retryable'] else 'permanent'}: {out['error']['message']}"
            if out["retryable"]:
                raise RuntimeError(msg)
            raise PermanentJobError(msg)
        return {"command_type": "pipeline.run_step", "ok": True, "step_id": p.get("step_id"),
                "artifacts": len(out["result"]["artifacts"])}
    if p.get("command_type") == "context.consume":
        # C-CONSUME-2: run the governed ingestion→consumption path as durable work through ConsumptionService.
        corpus = str(p.get("corpus") or "cfpb")
        if corpus != "cfpb":
            raise PermanentJobError(f"context.consume: unknown corpus {corpus!r} (only 'cfpb' is wired)")
        tenant = str(p.get("tenant_id") or "demo")
        snap = str(p.get("source_snapshot_hash") or f"{tenant}:{corpus}")
        first = store.mark_processed("consumption", snap)  # idempotency: a duplicate snapshot does not re-serve
        if not first:
            store.append_event({"seq": None, "kind": "context.consume.skipped", "stage": "Consumption",
                                "component": "flywheel_worker", "correlation_id": tenant, "object_ref": snap,
                                "payload": {"reason": "idempotent: source_snapshot already served"}})
            return {"command_type": "context.consume", "ok": True, "first_process": False, "skipped": True}
        from scripts.runtime.consumption import run_cfpb_to_consumption
        out = run_cfpb_to_consumption(tenant, require_optimized=bool(p.get("require_optimized", True)),
                                      now=str(p.get("now") or EPOCH_CONSUME))
        resp = out["response"]
        store.append_event({"seq": None, "kind": "context.response.created", "stage": "Consumption",
                            "component": "flywheel_worker", "correlation_id": tenant, "object_ref": resp["response_id"],
                            "payload": {"response_id": resp["response_id"], "answer": resp["answer"],
                                        "served_fact_count": len(resp["served_facts"]),
                                        "held_out_count": len(resp["held_out_warnings"]), "receipts": resp["receipts"]}})
        return {"command_type": "context.consume", "ok": True, "first_process": True,
                "response_id": resp["response_id"], "served_fact_count": len(resp["served_facts"]),
                "decision": out["decision"]}
    if p.get("command_type") in ("pipeline.run", "pipeline.step"):
        from scripts.pipeline_runtime.processors import default_registry
        from scripts.pipeline_runtime.runner import execute_command, run_step_command
        from scripts.pipeline_runtime.store import PipelineLedger
        ledger = PipelineLedger(store)
        if p["command_type"] == "pipeline.step":
            res = run_step_command(store, ledger, default_registry(), p)
        else:
            res = execute_command(store, ledger, default_registry(), p)
        store.append_event({"seq": None, "kind": "pipeline.completed" if res.get("status") == "done" else "pipeline.failed",
                            "stage": "Work plane", "component": "flywheel_worker",
                            "correlation_id": p.get("tenant_id"), "object_ref": res.get("run_id"),
                            "payload": {"pipeline": res.get("pipeline_ref"), "status": res.get("status")}})
        return {"run_id": res.get("run_id"), "pipeline_ref": res.get("pipeline_ref"), "status": res.get("status")}
    doc_id = str(p.get("doc_id") or job["id"])
    # idempotency guard — if this returns False the same doc was processed before (a real double-process).
    first = store.mark_processed("flywheel_worker", doc_id)
    facts = 0
    if first and isinstance(p.get("record"), dict):
        from scripts.ingest.decompose_structured import decompose_cfpb_complaint
        facts = decompose_cfpb_complaint(p["record"], native_id=doc_id)["fact_count"]
    store.append_event({"seq": None, "kind": "component.finished", "stage": "Work plane",
                        "component": "flywheel_worker", "correlation_id": p.get("tenant_id"),
                        "object_ref": doc_id, "payload": {"facts": facts, "first_process": first}})
    return {"doc_id": doc_id, "facts": facts, "first_process": first}


def work_once(store: DurableStore, queue: str, *, worker_id: str, now: int,
              handler: Callable[[DurableStore, dict], Any] = default_handler,
              lease_seconds: int = DEFAULT_LEASE_S) -> dict | None:
    """Claim one job → handler → ack (nack on error). Returns the result, or None if the queue is empty."""
    job = store.claim(queue, worker=worker_id, lease_seconds=lease_seconds, now=now)
    if job is None:
        return None
    try:
        res = handler(store, job)
        store.ack(job["id"])
        return {"ok": True, "job_id": job["id"], **(res if isinstance(res, dict) else {})}
    except PermanentJobError as e:  # can never succeed → dead-letter now, do not burn the retry budget
        status = store.nack(job["id"], error=f"{type(e).__name__}: {e}", permanent=True)
        return {"ok": False, "job_id": job["id"], "status": status, "error": str(e), "permanent": True}
    except Exception as e:  # noqa: BLE001 — bad job retries, then dead-letters; never crash the worker
        status = store.nack(job["id"], error=f"{type(e).__name__}: {e}")
        return {"ok": False, "job_id": job["id"], "status": status, "error": str(e)}


def run_worker(store: DurableStore, queue: str, *, worker_id: str,
               handler: Callable[[DurableStore, dict], Any] = default_handler,
               lease_seconds: int = DEFAULT_LEASE_S, max_empty: int = DEFAULT_MAX_EMPTY,
               idle: float = DEFAULT_IDLE_S, max_jobs: int | None = None, now_fn: Callable[[], int] | None = None) -> dict:
    """Run the claim-loop until ``max_empty`` consecutive empty polls (or ``max_jobs``). Returns a summary."""
    now_fn = now_fn or (lambda: int(time.time()))
    processed, failed, empty = 0, 0, 0
    while True:
        res = work_once(store, queue, worker_id=worker_id, now=now_fn(), handler=handler, lease_seconds=lease_seconds)
        if res is None:
            empty += 1
            if empty >= max_empty:
                break
            time.sleep(idle)
            continue
        empty = 0
        processed += 1 if res.get("ok") else 0
        failed += 0 if res.get("ok") else 1
        if max_jobs and processed >= max_jobs:
            break
    return {"worker_id": worker_id, "queue": queue, "processed": processed, "failed": failed}


def _self_test() -> int:
    import tempfile
    import shutil

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="fw-worker-")
    store = DurableStore(tmp + "/d.db")
    for i in range(5):
        store.enqueue("q", {"doc_id": f"d{i}", "record": {"product": "x", "issue": f"i{i}", "company": "c", "state": "CA"}})
    summary = run_worker(store, "q", worker_id="w1", now_fn=lambda: 100)
    check("worker drained all 5 jobs", summary["processed"] == 5 and summary["failed"] == 0, str(summary))
    check("queue done=5, queued=0", store.stats("q")["done"] == 5 and store.stats("q")["queued"] == 0)
    fin = [e for e in store.recent_events(50) if e["kind"] == "component.finished"]
    check("each job emitted exactly one Work-plane event (no double-process)",
          sorted(e["object_ref"] for e in fin) == ["d0", "d1", "d2", "d3", "d4"])
    check("all marked first_process=True (idempotent, no re-run)", all(e["payload"]["first_process"] for e in fin))
    check("empty queue → worker exits (returns summary)", run_worker(store, "q", worker_id="w2", now_fn=lambda: 200)["processed"] == 0)

    # poison job → retries then DLQ (handler raises)
    store.enqueue("poison", {"doc_id": "bad"}, max_attempts=2)

    def _boom(_s, _j):
        raise ValueError("boom")

    run_worker(store, "poison", worker_id="w", handler=_boom, now_fn=lambda: 0, max_empty=1)
    check("poison job dead-lettered after retry budget", store.stats("poison")["dead"] == 1, str(store.stats("poison")))

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'all flywheel_worker self-tests passed (claim-loop drains queue, exactly-once events, idle-exit, poison→DLQ).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Standalone durable worker: claim-loop drains a durable queue.")
    p.add_argument("--db", help="durable sqlite db path")
    p.add_argument("--queue", help="queue to drain")
    p.add_argument("--worker-id", default="worker")
    p.add_argument("--max-empty", type=int, default=DEFAULT_MAX_EMPTY)
    p.add_argument("--lease", type=int, default=DEFAULT_LEASE_S)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not (args.db and args.queue):
        p.error("--db and --queue are required (or use --self-test)")
    store = DurableStore(args.db)
    summary = run_worker(store, args.queue, worker_id=args.worker_id, lease_seconds=args.lease, max_empty=args.max_empty)
    store.close()
    import json
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
