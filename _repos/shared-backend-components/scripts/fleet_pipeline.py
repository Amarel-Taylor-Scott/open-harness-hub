#!/usr/bin/env python3
"""scripts.fleet_pipeline — THE JOIN (G1): the full context pipeline run AS FLEET WORK.

`run_full_pipeline` (in the admin server) composes the shipped engines INLINE. This runs the SAME engines,
but every stage (Intake → Decomposition → Reconciliation → Anti-Fragility → Enhancement → Verification →
Consumption) is enqueued as a CapabilityTask in the FleetLedger and executed ONLY after a worker wins the
ATOMIC CLAIM — under a supervisor spawn/use-existing decision. So the components don't just exist as a
proven fleet AND as engine functions: the demo actually runs them as claimed fleet tasks.

Offline, deterministic, no Redis/network. Emits the same dashboard events to the in-process bus.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/fleet_pipeline.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse

from scripts.context_compress import compress
from scripts.context_events import EventBus
from scripts.context_graph import ContextGraph, interrogate, load_seed
from scripts.context_swarm import swarm_object
from scripts.source_expansion import expand_source_handle
from src.baltor.workers import spawn_decision
from src.baltor.workers.fleet_ledger import FleetLedger, _plus_s

T0 = "2026-06-06T00:00:00Z"
RETRY_Q = "What is the retry ceiling / how many retries are allowed?"
CID = "pipeline-acme-fleet"


# ── stage functions: each calls a REAL engine; runs UNDER an atomic claim (task_id is the proof) ──
def _intake(ctx, bus, task_id):
    g = ContextGraph(load_seed())
    ctx["g"] = g
    for oid, o in g.objects.items():
        for h in (o.get("source_handles") or [])[:1]:
            bus.publish("source_handle.created", component="ingest", stage="Source Systems",
                        correlation_id=CID, object_ref=oid, payload={"handle": h, "task_id": task_id})


def _decompose(ctx, bus, task_id):
    g = ctx["g"]
    for oid, o in g.objects.items():
        bus.publish("context_object.created", component="decompose", stage="Source Systems",
                    correlation_id=CID, object_ref=oid, payload={"type": o.get("object_type"), "task_id": task_id})


def _reconcile(ctx, bus, task_id):
    g = ctx["g"]
    interro = interrogate(g, RETRY_Q, bus=bus)
    ctx["interro"] = interro
    ctx["answer"] = interro["answer_value"]
    ctx["items"] = [{"ref": oid,
                     "text": f"{g.objects[oid].get('title', '')}. {g.objects[oid].get('summary', '')} {g.objects[oid].get('claim', '')}",
                     "source_handles": g.objects[oid].get("source_handles", [])}
                    for oid in interro.get("objects_consulted", []) if oid in g.objects]


def _fragility(ctx, bus, task_id):
    sw = swarm_object(ctx["g"], "obj-runbook", bus=bus)
    ctx["sw"] = sw
    for rr in sw["review_requests"]:
        bus.publish("review.requested", component="fragility", stage="Anti-Fragility", correlation_id=CID,
                    object_ref=rr.get("subject"), payload={"trigger": rr.get("trigger"), "task_id": task_id})


def _enhance(ctx, bus, task_id):
    items = ctx.get("items") or []
    ctx["pack"] = (compress(items, query="retry ceiling retries", max_tokens=256, bus=bus)
                   if items else {"token_budget": {"estimated_before": 0, "estimated_after": 0}, "retained_refs": []})


def _verify(ctx, bus, task_id):
    expand_source_handle("ctx://acme-billing/decisions/ADR-014-billing-retry-policy.md#decision",
                         classification="internal", bus=bus)
    expand_source_handle("ctx://acme-billing/docs/billing-runbook.md#retry-policy",
                         classification="regulated", bus=bus)
    from scripts.pipeline.verified_context_flow import (
        DEMO_INTERNAL_CLAIMS, DEMO_SOURCE_RECORDS, run as run_verified_context_flow,
    )
    run_verified_context_flow(DEMO_SOURCE_RECORDS, DEMO_INTERNAL_CLAIMS, bus=bus)
    ctx["verified"] = True


def _consume(ctx, bus, task_id):
    interro = ctx["interro"]
    bus.publish("receipt_issued", component="consume", stage="Consumption", correlation_id=CID,
                payload={"answer_value": interro["answer_value"],
                         "authority": (interro["authority"] or {}).get("subject_id"), "task_id": task_id})
    from scripts.eval.context_lift_matrix import CORPUS_ITEMS, run_matrix
    matrix = run_matrix(items=CORPUS_ITEMS["acme"])
    cm = matrix["by_model"]["local_mock"]["condition_mean"]
    ctx["lift"] = round((cm.get("context_pack") or 0.0) - (cm.get("no_context") or 0.0), 4)


STAGES = [
    ("intake.load", "Intake", _intake),
    ("decompose.objects", "Decomposition", _decompose),
    ("reconcile.interrogate", "Reconciliation", _reconcile),
    ("fragility.detect", "Anti-Fragility", _fragility),
    ("enhance.compress", "Enhancement", _enhance),
    ("verify.flow", "Verification", _verify),
    ("consume.receipt", "Consumption", _consume),
]
CAPS = [c for c, _, _ in STAGES]


def run_full_pipeline_via_fleet(*, bus=None, ledger=None) -> dict:
    """Run every pipeline stage as a CapabilityTask claimed atomically by a worker (under a supervisor
    decision). Returns the run summary incl. which stages ran via which claimed task."""
    bus = bus or EventBus()
    ledger = ledger or FleetLedger()
    ctx: dict = {}
    bus.publish("pipeline.started", component="pipeline", stage="Source Systems", correlation_id=CID,
                payload={"corpus": "acme-billing", "via": "fleet"})

    worker_id = "fleet-pipeline-worker"
    ledger.register_worker(worker_id=worker_id, capability_ids=CAPS, max_concurrency=4, now=T0)
    ledger.set_worker_status(worker_id, "warm", now=T0)

    ran: list[dict] = []
    now = T0
    for i, (cap, label, fn) in enumerate(STAGES):
        task = ledger.enqueue_task(tenant_id="demo", capability_id=cap, idempotency_key=f"stage-{i}-{cap}",
                                   now=now, priority_class="P1")
        # supervisor decides (warm worker meets SLA → use_existing); recorded as the scheduling intent
        dec = spawn_decision.decide(
            capability_id=cap,
            queued=[{"task_id": task["task_id"], "capability_id": cap, "priority_class": "P1", "created_at": now, "deadline_at": None}],
            workers=[{"worker_id": worker_id, "status": "warm", "capability_ids": CAPS, "available_at": now,
                      "max_concurrency": 4, "active_task_count": 0}],
            now=now, lifecycle={"startup_budget_ms": 3000, "max_workers": 10},
            batch={"batch_min": 1, "max_wait_seconds": 0}, sla={"target_seconds": 120},
            estimated_runtime_ms=500, known_capabilities=set(CAPS))
        # OWNERSHIP BEGINS ONLY HERE — the worker must win the atomic claim before the engine runs
        claim = ledger.claim_task(worker_id=worker_id, capability_id=cap, now=now)
        if claim is None or claim["task_id"] != task["task_id"]:
            raise RuntimeError(f"stage {cap}: atomic claim failed")
        ledger.start_task(task["task_id"], worker_id, now)
        fn(ctx, bus, task["task_id"])                       # the REAL engine runs under the claim
        ledger.ack_task(task["task_id"], worker_id, [], now)
        ran.append({"capability": cap, "stage": label, "task_id": task["task_id"], "decision": dec["action"]})
        now = _plus_s(now, 1)

    bus.publish("pipeline.completed", component="pipeline", stage="Consumption", correlation_id=CID,
                payload={"answer_value": ctx.get("answer"), "lift": ctx.get("lift"), "via": "fleet"})
    return {
        "ok": True, "via_fleet": True, "answer_value": ctx.get("answer"), "lift": ctx.get("lift"),
        "correlation_id": CID, "stages": ran,
        "events_emitted": len(bus.by_correlation(CID)),
        "succeeded_tasks": len(ledger.tasks_by_status("succeeded")),
        "worker_processed": ledger._workers[worker_id]["total_tasks_processed"],
    }


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    bus = EventBus()
    ledger = FleetLedger()
    out = run_full_pipeline_via_fleet(bus=bus, ledger=ledger)

    chk("pipeline ran via the fleet", out["via_fleet"] and out["ok"])
    chk("all 7 stages ran", len(out["stages"]) == 7, str(len(out["stages"])))
    chk("every stage ran UNDER a claimed task (worker processed all 7)", out["worker_processed"] == 7, str(out["worker_processed"]))
    chk("every stage task SUCCEEDED in the ledger", out["succeeded_tasks"] == 7, str(out["succeeded_tasks"]))
    # each stage's task went QUEUED→CLAIMED→RUNNING→SUCCEEDED owned by the worker (not inline)
    for s in out["stages"]:
        t = ledger.task(s["task_id"])
        chk(f"stage {s['capability']} owned+succeeded via claim", t and t["status"] == "succeeded" and t["lease_owner"] == "fleet-pipeline-worker")
    chk("supervisor used the warm worker (use_existing)", all(s["decision"] == "use_existing_worker" for s in out["stages"]),
        str({s["capability"]: s["decision"] for s in out["stages"]}))

    # the REFERENCE answer still holds end-to-end
    chk("reference answer preserved (retry ceiling = 5)", str(out["answer_value"]) == "5", str(out["answer_value"]))

    # the components actually fired their dashboard events
    kinds = {e["kind"] for e in bus.by_correlation(CID)}
    for k in ("pipeline.started", "context_object.created", "review.requested", "receipt_issued", "pipeline.completed"):
        chk(f"emitted {k}", k in kinds)

    # wired into the dashboard run path
    from pathlib import Path
    srv = (_resource("scripts/baltor_admin_demo_server.py")).read_text()
    chk("admin server exposes /api/demo/run-full-pipeline-via-fleet", "/api/demo/run-full-pipeline-via-fleet" in srv)
    chk("route calls run_full_pipeline_via_fleet on the live bus", "run_full_pipeline_via_fleet(bus=BUS)" in srv)
    dash = (_resource("web/baltor/dashboard.html")).read_text()
    chk("dashboard has a Run via Fleet button", 'id="run-fleet"' in dash and "Run via Fleet" in dash)
    chk("dashboard button calls the fleet route", "/api/demo/run-full-pipeline-via-fleet" in dash)

    # determinism
    out2 = run_full_pipeline_via_fleet(bus=EventBus(), ledger=FleetLedger())
    chk("deterministic answer + stage set", str(out2["answer_value"]) == "5" and len(out2["stages"]) == 7)

    print(f"\n{'PASS — fleet_pipeline: all 7 stages run as CapabilityTasks claimed atomically by a worker under supervisor decisions; reference answer preserved; same dashboard events fire.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
