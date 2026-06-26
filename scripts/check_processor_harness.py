#!/usr/bin/env python3
"""scripts.check_processor_harness — proof: the harness runs a processor, validates command + result +
artifacts, writes/publishes through ports, and classifies failures (exception → retryable; unknown
processor / bad schema → permanent) into ErrorEnvelopes.

CLI: python3 scripts/check_processor_harness.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.context import build_context
from scripts.runtime.envelopes import CommandEnvelope, ProcessorResult
from scripts.runtime.processor import Processor, ProcessorSpec
from scripts.runtime.processor_harness import run_command
from scripts.runtime.processor_registry import default_registry


class BoomProcessor(Processor):
    spec = ProcessorSpec("test.boom", "v1")

    def handle(self, command, ctx):
        raise RuntimeError("kaboom")


def _cmd(processor_id, version, *, run_id="run-1", step="s", payload=None) -> CommandEnvelope:
    return CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id=run_id, queue="q",
                           step_id=step, processor_id=processor_id, processor_version=version, payload=payload or {})


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = default_registry()
    reg.register(BoomProcessor())

    # success path: graph stub emits an event; harness validates + publishes
    ctx = build_context(tenant_id="acme", run_id="run-1", step_id="graph")
    ok = run_command(reg, _cmd("graph.deterministic_edges", "v1", step="graph", payload={"edge_count": 3}), ctx)
    check("harness runs a processor successfully", ok["ok"] and ok["status"] == "ok", str(ok.get("error")))
    check("harness validated the ProcessorResult", ok["result"]["schema_version"] == "ProcessorResult")
    check("emitted event published through the event_bus port", len(ctx.event_bus.events) == 1)
    check("structured log span recorded (started + completed)",
          any(r["event"] == "pipeline.step.completed" for r in ctx.logger.records))

    # CFPB decompose through the harness — emitted artifacts validate + are written
    ctx2 = build_context(tenant_id="acme", run_id="run-2", step_id="decompose")
    rec = {"complaint_id": "C1", "product": "Credit card", "issue": "Billing", "company": "Acme",
           "consumer_complaint_narrative": "Charged twice. No refund."}
    ok2 = run_command(reg, _cmd("decompose.cfpb_structured", "v1", run_id="run-2", step="decompose",
                                payload={"records": [rec]}), ctx2)
    check("harness ran decompose + validated every emitted artifact", ok2["ok"] and len(ok2["result"]["artifacts"]) > 0)
    check("artifacts were written through the artifact_store port", len(ctx2.artifact_store.artifacts) == len(ok2["result"]["artifacts"]))

    # exception → retryable ErrorEnvelope
    boom = run_command(reg, _cmd("test.boom", "v1"), build_context(tenant_id="acme", run_id="run-1"))
    check("a processor exception → retryable ErrorEnvelope", (not boom["ok"]) and boom["retryable"] is True
          and boom["error"]["error_type"] == "processor_exception")

    # unknown processor → permanent
    unk = run_command(reg, _cmd("nope.missing", "v9"), build_context(tenant_id="acme", run_id="run-1"))
    check("an unknown processor → permanent unavailable_processor", (not unk["ok"]) and unk["retryable"] is False
          and unk["error"]["error_type"] == "unavailable_processor")

    # invalid command (missing run_id) → permanent schema failure
    bad = dict(_cmd("graph.deterministic_edges", "v1").to_dict()); bad.pop("run_id")
    badres = run_command(reg, bad, build_context(tenant_id="acme", run_id="x"))
    check("an invalid command → permanent schema_validation_failed", (not badres["ok"]) and badres["retryable"] is False
          and badres["error"]["error_type"] == "schema_validation_failed")

    print(f"\n{'PASS — check_processor_harness: runs processors, validates command/result/artifacts, publishes via ports, and classifies exception(retryable)/unknown/bad-schema(permanent) into ErrorEnvelopes.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: processor harness lifecycle + error classification.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
