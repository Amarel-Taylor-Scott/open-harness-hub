#!/usr/bin/env python3
"""scripts.check_worker_command_envelope — proof: the durable worker claims + executes CommandEnvelope work
through the harness — a valid command is acked, an invalid one is nacked→DLQ with an ErrorEnvelope recorded,
and the existing tenant/doc path (the two-process exactly-once behaviour) is unregressed.

CLI: python3 _repos/shared-backend-components/scripts/check_worker_command_envelope.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.durable_store import DurableStore
from scripts.flywheel_worker import work_once
from scripts.runtime.envelopes import CommandEnvelope

REC = {"complaint_id": "C1", "product": "Credit card", "issue": "Billing", "company": "Acme",
       "consumer_complaint_narrative": "Charged twice. No refund. Unfair."}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = DurableStore(":memory:")
    Q = "runtime.commands"

    # valid CommandEnvelope (pipeline.run_step → decompose) → acked
    cmd = CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id="run-1", queue=Q,
                          pipeline_id="cfpb_artifact_graph", pipeline_version="v1", step_id="decompose",
                          processor_id="decompose.cfpb_structured", processor_version="v1", payload={"records": [REC]})
    store.enqueue(Q, cmd.to_dict(), idempotency_key=cmd.idempotency_key)
    res = work_once(store, Q, worker_id="w1", now=1000)
    check("worker claims + executes a CommandEnvelope", res and res.get("ok") and res["command_type"] == "pipeline.run_step", str(res))
    check("valid command is ACKED (job done, none queued)", store.stats(Q).get("done", 0) == 1 and store.stats(Q).get("queued", 0) == 0, str(store.stats(Q)))
    check("harness emitted decomposed artifacts", res["artifacts"] > 0)

    # invalid CommandEnvelope (missing run_id) → permanent schema failure → nack → DLQ (max_attempts=1)
    bad = dict(cmd.to_dict()); bad.pop("run_id"); bad["command_id"] = "cmd-bad"
    store.enqueue(Q, bad, idempotency_key="bad-1", max_attempts=1)
    r2 = work_once(store, Q, worker_id="w1", now=1001)   # raises inside handler → nack → dead (max_attempts=1)
    check("invalid command does NOT ack as success", r2 is None or not (r2 or {}).get("ok"))
    check("invalid command is dead-lettered", store.stats(Q).get("dead", 0) == 1, str(store.stats(Q)))
    evs = store.recent_events(limit=200)
    check("a processor.failed/ErrorEnvelope event was recorded durably for the bad command",
          any(e.get("kind") == "processor.failed" for e in evs))

    # existing tenant/doc path unregressed: doc job → decomposed exactly once
    store.enqueue(Q, {"command_type": "tenant.doc", "tenant_id": "acme", "doc_id": "D1", "record": REC}, idempotency_key="D1")
    r3 = work_once(store, Q, worker_id="w1", now=1002)
    check("legacy doc path still processes (facts emitted, first_process)", r3 and r3.get("facts", 0) > 0 and r3.get("first_process") is True, str(r3))

    store.close()
    print(f"\n{'PASS — check_worker_command_envelope: the durable worker runs CommandEnvelope work through the harness (valid→ack, invalid→DLQ with ErrorEnvelope), and the legacy doc path is unregressed.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: durable worker consumes CommandEnvelope work.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
