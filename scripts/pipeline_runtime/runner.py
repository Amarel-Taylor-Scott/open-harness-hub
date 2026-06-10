#!/usr/bin/env python3
"""scripts.pipeline_runtime.runner — execute a versioned pipeline run, durably + idempotently.

The generic engine: load a PipelineSpec → derive an idempotency key from BOTH the input hash AND the
pipeline version (a changed document OR a changed pipeline config ⇒ a distinct run = reprocessing) →
execute each step through the ProcessorRegistry (never importing processors directly) → write
content-addressed artifacts → record step_runs → evaluate gates → finish the run. Reusable by the HTTP
route (inline) and by the standalone worker (durable command). The ledger + artifacts are the source of
truth; the dashboard is a projection.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from scripts.context_events import emit
from scripts.foundry.scrapers import content_hash
from scripts.pipeline_runtime.specs import PipelineSpec, discover
from scripts.pipeline_runtime.store import PipelineLedger


def idempotency_key(spec: PipelineSpec, tenant_id: str, run_input: dict) -> tuple[str, str]:
    input_hash = content_hash(_canon(run_input))
    ctx = {"tenant_id": tenant_id, "source_id": str(run_input.get("source_id", "batch")),
           "document_version": input_hash[:12], "pipeline_id": spec.pipeline_id,
           "pipeline_version": spec.pipeline_version}
    tmpl = spec.idempotency_key_template or "{tenant_id}:{source_id}:{document_version}:{pipeline_id}:{pipeline_version}"
    return tmpl.format_map(_Default(ctx)), input_hash


def _canon(v: Any) -> str:
    import json
    return json.dumps(v, sort_keys=True, default=str)


class _Default(dict):
    def __missing__(self, k):  # tolerate template keys we didn't supply
        return "{" + k + "}"


# ── gates (declared in the manifest; evaluated over produced artifacts) ───────
def _gate_all_facts_handled(arts: dict) -> bool:
    return all("#" in f.get("source_handle", "") for f in arts.get("AtomicFactSet.v1", {}).get("facts", []))


def _gate_narratives_not_promotable(arts: dict) -> bool:
    return all(not a.get("promotion_eligible", False) for a in arts.get("HeldOutAllegationSet.v1", {}).get("allegations", []))


def _gate_receipt_counts_match(arts: dict) -> bool:
    rc = arts.get("Receipt.v1", {})
    return rc.get("facts_served") == arts.get("VerifiedFactSet.v1", {}).get("count")


def _gate_doc_tree_leaves(arts: dict) -> bool:
    t = arts.get("DocumentTree.v1", {})
    return t.get("node_count", 0) > 0 and bool(t.get("leaf_handles")) and all("#" in h for h in t.get("leaf_handles", []))


GATES = {
    "all_atomic_facts_have_source_handles": _gate_all_facts_handled,
    "narratives_are_not_promotion_eligible": _gate_narratives_not_promotable,
    "pack_receipt_counts_match_fact_counts": _gate_receipt_counts_match,
    "document_tree_has_addressable_leaves": _gate_doc_tree_leaves,
}


def run_pipeline(spec: PipelineSpec, *, tenant_id: str, run_input: dict, ledger: PipelineLedger,
                 registry, bus=None, clock: str = "") -> dict:
    """Execute a pipeline INLINE, recording the durable run/step/artifact ledger. Idempotent per key."""
    idk, input_hash = idempotency_key(spec, tenant_id, run_input)
    run_id = "run-" + content_hash(idk)[:12]
    created = ledger.create_run(run_id=run_id, pipeline_id=spec.pipeline_id, pipeline_version=spec.pipeline_version,
                                tenant_id=tenant_id, input_hash=input_hash, idempotency_key=idk, started_at=clock)
    if created["duplicate"]:
        existing = ledger.get_run(created["run_id"])
        return {"run_id": created["run_id"], "duplicate": True, "status": (existing or {}).get("status"),
                "pipeline_ref": spec.ref}

    emit(bus, "pipeline.started", component="pipeline_runtime", stage="Source Systems",
         correlation_id=run_id, payload={"pipeline": spec.ref, "tenant": tenant_id})
    arts_by_type: dict[str, Any] = {}
    art_id_by_type: dict[str, str] = {}
    queued_steps = 0
    try:
        for step in _ordered(spec.steps):
            queued_steps += 1
            input_ids = [art_id_by_type[t] for t in step.input_artifact_types if t in art_id_by_type]
            sr = ledger.start_step(run_id=run_id, step_id=step.step_id, processor_id=step.processor_id,
                                   processor_version=step.processor_version, input_artifact_ids=input_ids, started_at=clock)
            pspec = registry.spec(step.processor_ref)
            if pspec is not None and not pspec.available:
                msg = f"unavailable_processor: {step.processor_ref} — {pspec.unavailable_reason}"
                ledger.finish_step(sr, status="failed", output_artifact_ids=[], error=msg, finished_at=clock)
                ledger.finish_run(run_id, status="failed", error={"step": step.step_id, "reason": msg}, finished_at=clock)
                emit(bus, "pipeline.failed", component="pipeline_runtime", stage="Source Systems",
                     correlation_id=run_id, payload={"pipeline": spec.ref, "error": msg})
                return {"run_id": run_id, "duplicate": False, "status": "failed", "error": msg, "pipeline_ref": spec.ref}
            fn = registry.get(step.processor_ref)
            outputs = fn(dict(arts_by_type), config=run_input, run={"run_id": run_id, "tenant_id": tenant_id, "pipeline_ref": spec.ref})
            missing = [t for t in step.output_artifact_types if t not in outputs]
            if missing:
                raise ValueError(f"step {step.step_id} did not produce declared outputs {missing}")
            out_ids = []
            for atype, payload in outputs.items():
                handles = payload.get("source_handles") if isinstance(payload, dict) else None
                rec = ledger.put_artifact(artifact_type=atype, schema_version=atype.split(".")[-1], payload=payload,
                                          created_by_step_run_id=sr, source_handles=handles, created_at=clock)
                arts_by_type[atype] = payload
                art_id_by_type[atype] = rec["artifact_id"]
                out_ids.append(rec["artifact_id"])
            ledger.finish_step(sr, status="done", output_artifact_ids=out_ids, finished_at=clock)
            emit(bus, "component.progressed", component="pipeline_runtime", stage="Work plane",
                 correlation_id=run_id, payload={"step": step.step_id, "processor": step.processor_ref, "outputs": list(outputs)})

        gate_results = {g: bool(GATES[g](arts_by_type)) for g in spec.gates if g in GATES}
        failed_gates = [g for g, ok in gate_results.items() if not ok]
        terminal = arts_by_type.get(spec.output_schema) or (list(arts_by_type.values())[-1] if arts_by_type else {})
        output_hash = content_hash(_canon(terminal))
        status = "failed" if failed_gates else "done"
        ledger.finish_run(run_id, status=status, output_hash=output_hash,
                          error=({"failed_gates": failed_gates} if failed_gates else None), finished_at=clock)
        emit(bus, "pipeline.completed" if status == "done" else "pipeline.failed", component="pipeline_runtime",
             stage="Consumption", correlation_id=run_id, payload={"pipeline": spec.ref, "status": status, "gates": gate_results})
        return {"run_id": run_id, "duplicate": False, "status": status, "pipeline_ref": spec.ref,
                "queued_steps": queued_steps, "artifact_count": len(art_id_by_type),
                "artifact_ids": dict(art_id_by_type), "output_hash": output_hash,
                "gates": gate_results, "failed_gates": failed_gates}
    except Exception as e:  # noqa: BLE001
        ledger.finish_run(run_id, status="failed", error={"exception": f"{type(e).__name__}: {e}"}, finished_at=clock)
        emit(bus, "pipeline.failed", component="pipeline_runtime", stage="Work plane",
             correlation_id=run_id, payload={"pipeline": spec.ref, "error": str(e)})
        return {"run_id": run_id, "duplicate": False, "status": "failed", "error": str(e), "pipeline_ref": spec.ref}


def _ordered(steps: list) -> list:
    """Topological-ish order honoring depends_on (manifests are mostly linear)."""
    done, out, remaining = set(), [], list(steps)
    while remaining:
        progressed = False
        for s in list(remaining):
            if all(d in done for d in s.depends_on):
                out.append(s)
                done.add(s.step_id)
                remaining.remove(s)
                progressed = True
        if not progressed:  # cycle / dangling dep → append the rest in declared order
            out.extend(remaining)
            break
    return out


# ── PER-STEP queue routing (each step its own lane; worker runs one step + enqueues the next) ──
def _step_queue(step, prefix: str = "flywheel.commands") -> str:
    return step.queue or f"{prefix}.{step.step_id}"


def step_queues(spec: PipelineSpec) -> list[str]:
    return [_step_queue(s) for s in spec.steps]


def _enqueue_ready_steps(durable, ledger: PipelineLedger, spec: PipelineSpec, run_id: str,
                         tenant_id: str, run_input: dict) -> list[str]:
    """Enqueue every step whose deps are all DONE and that has not been started/enqueued (idempotent)."""
    statuses = ledger.step_statuses(run_id)
    done = {s for s, st in statuses.items() if st == "done"}
    started = set(statuses)
    enq: list[str] = []
    for step in spec.steps:
        if step.step_id in started or not all(d in done for d in step.depends_on):
            continue
        payload = {"command_type": "pipeline.step", "run_id": run_id, "pipeline_ref": spec.ref,
                   "step_id": step.step_id, "tenant_id": tenant_id, "run_input": run_input}
        durable.enqueue(_step_queue(step), payload, idempotency_key=f"step:{run_id}:{step.step_id}")
        enq.append(step.step_id)
    return enq


def start_run_via_queue(durable, ledger: PipelineLedger, spec: PipelineSpec, *, tenant_id: str,
                        run_input: dict, clock: str = "") -> dict:
    """Create a run and enqueue its first ready step(s). Steps then flow step→queue→worker→next-step."""
    idk, input_hash = idempotency_key(spec, tenant_id, run_input)
    run_id = "run-" + content_hash(idk)[:12]
    created = ledger.create_run(run_id=run_id, pipeline_id=spec.pipeline_id, pipeline_version=spec.pipeline_version,
                               tenant_id=tenant_id, input_hash=input_hash, idempotency_key=idk, started_at=clock)
    if created["duplicate"]:
        return {"run_id": created["run_id"], "duplicate": True}
    enq = _enqueue_ready_steps(durable, ledger, spec, run_id, tenant_id, run_input)
    return {"run_id": run_id, "duplicate": False, "enqueued_steps": enq, "step_queues": step_queues(spec)}


def run_step_command(durable, ledger: PipelineLedger, registry, payload: dict, *, bus=None, clock: str = "") -> dict:
    """Worker handler for ONE `pipeline.step` command: execute the step, write artifacts, enqueue the next
    ready step(s), finish the run when all steps are done. Idempotent (a re-delivered done step is skipped)."""
    spec = discover().get(payload["pipeline_ref"])
    step = next(s for s in spec.steps if s.step_id == payload["step_id"])
    run_id = payload["run_id"]
    if ledger.step_statuses(run_id).get(step.step_id) == "done":
        return {"run_id": run_id, "step": step.step_id, "status": "already_done"}
    inputs = ledger.run_artifacts(run_id)
    sr = ledger.start_step(run_id=run_id, step_id=step.step_id, processor_id=step.processor_id,
                           processor_version=step.processor_version, input_artifact_ids=[], started_at=clock)
    pspec = registry.spec(step.processor_ref)
    if pspec is not None and not pspec.available:
        msg = f"unavailable_processor: {step.processor_ref} — {pspec.unavailable_reason}"
        ledger.finish_step(sr, status="failed", output_artifact_ids=[], error=msg, finished_at=clock)
        ledger.finish_run(run_id, status="failed", error={"step": step.step_id, "reason": msg}, finished_at=clock)
        return {"run_id": run_id, "step": step.step_id, "status": "failed", "error": msg}
    try:
        outputs = registry.get(step.processor_ref)(inputs, config=payload.get("run_input", {}),
                                                   run={"run_id": run_id, "tenant_id": payload["tenant_id"], "pipeline_ref": spec.ref})
        missing = [t for t in step.output_artifact_types if t not in outputs]
        if missing:
            raise ValueError(f"step {step.step_id} did not produce declared outputs {missing}")
        out_ids = []
        for atype, pl in outputs.items():
            handles = pl.get("source_handles") if isinstance(pl, dict) else None
            rec = ledger.put_artifact(artifact_type=atype, schema_version=atype.split(".")[-1], payload=pl,
                                      created_by_step_run_id=sr, source_handles=handles, created_at=clock)
            out_ids.append(rec["artifact_id"])
        ledger.finish_step(sr, status="done", output_artifact_ids=out_ids, finished_at=clock)
        emit(bus, "component.progressed", component="pipeline_runtime", stage="Work plane",
             correlation_id=run_id, payload={"step": step.step_id, "processor": step.processor_ref})
    except Exception as e:  # noqa: BLE001
        ledger.finish_step(sr, status="failed", output_artifact_ids=[], error=str(e), finished_at=clock)
        ledger.finish_run(run_id, status="failed", error={"step": step.step_id, "exception": str(e)}, finished_at=clock)
        return {"run_id": run_id, "step": step.step_id, "status": "failed", "error": str(e)}
    newly = _enqueue_ready_steps(durable, ledger, spec, run_id, payload["tenant_id"], payload.get("run_input", {}))
    statuses = ledger.step_statuses(run_id)
    if all(statuses.get(s.step_id) == "done" for s in spec.steps):
        arts = ledger.run_artifacts(run_id)
        gres = {g: bool(GATES[g](arts)) for g in spec.gates if g in GATES}
        failed = [g for g, ok in gres.items() if not ok]
        terminal = arts.get(spec.output_schema) or {}
        ledger.finish_run(run_id, status=("failed" if failed else "done"), output_hash=content_hash(_canon(terminal)),
                          error=({"failed_gates": failed} if failed else None), finished_at=clock)
        emit(bus, "pipeline.completed" if not failed else "pipeline.failed", component="pipeline_runtime",
             stage="Consumption", correlation_id=run_id, payload={"pipeline": spec.ref, "gates": gres})
    return {"run_id": run_id, "step": step.step_id, "status": "done", "enqueued_next": newly}


def drain_steps(durable, ledger: PipelineLedger, registry, *, queues: list[str], now: int,
                worker: str = "step-worker", max_iters: int = 500, bus=None) -> list[tuple]:
    """Drive per-step queues to completion (a single-process driver; in a fleet each queue = a Deployment)."""
    processed: list[tuple] = []
    for _ in range(max_iters):
        any_work = False
        for q in queues:
            job = durable.claim(q, worker=worker, lease_seconds=60, now=now)
            if job:
                any_work = True
                res = run_step_command(durable, ledger, registry, job["payload"], bus=bus)
                durable.ack(job["id"])
                processed.append((q, res.get("step"), res.get("status")))
        if not any_work:
            break
    return processed


# ── durable command path (the worker drains these) ───────────────────────────
def enqueue_run(durable, *, pipeline_ref: str, tenant_id: str, run_input: dict, queue: str = "pipeline.runs",
                idempotency_suffix: str = "") -> dict:
    """Enqueue a pipeline run as a durable work item (idempotent per run key)."""
    specs = discover()
    spec = specs.get(pipeline_ref)
    if spec is None:
        raise KeyError(f"unknown pipeline {pipeline_ref}")
    idk, _ = idempotency_key(spec, tenant_id, run_input)
    payload = {"command_type": "pipeline.run", "pipeline_ref": pipeline_ref, "tenant_id": tenant_id, "run_input": run_input}
    res = durable.enqueue(queue, payload, idempotency_key="cmd:" + idk + idempotency_suffix)
    return {"queue": queue, "job_id": res["id"], "duplicate": res["duplicate"], "pipeline_ref": pipeline_ref}


def run_lineage(ledger: PipelineLedger, durable, run_id: str) -> dict | None:
    """Assemble a run's full lineage projection: run + step_runs + artifacts + OTel span tree (from the
    run's persisted events). Read-only — the ledger + durable event log are the source of truth."""
    run = ledger.get_run(run_id)
    if not run:
        return None
    from scripts.pipeline_runtime.envelope import chain_events
    from scripts.pipeline_runtime.otel import to_otel_spans
    spans = to_otel_spans(chain_events(durable.events_by_correlation(run_id)))
    artifacts = []
    for st in run["steps"]:
        for aid in st.get("output_artifact_ids", []):
            a = ledger.get_artifact(aid)
            if a:
                artifacts.append({"artifact_id": a["artifact_id"], "artifact_type": a["artifact_type"],
                                  "content_hash": a["content_hash"], "source_handles": a["source_handles"],
                                  "step_id": st["step_id"]})
    return {"run": run, "artifacts": artifacts, "spans": spans, "span_count": len(spans)}


def execute_command(durable, ledger: PipelineLedger, registry, command_payload: dict, *, bus=None, clock: str = "") -> dict:
    """Worker handler for a `pipeline.run` command: load spec from manifests + run it."""
    spec = discover().get(command_payload["pipeline_ref"])
    if spec is None:
        raise KeyError(f"unknown pipeline {command_payload['pipeline_ref']}")
    return run_pipeline(spec, tenant_id=command_payload["tenant_id"], run_input=command_payload.get("run_input", {}),
                        ledger=ledger, registry=registry, bus=bus, clock=clock)
