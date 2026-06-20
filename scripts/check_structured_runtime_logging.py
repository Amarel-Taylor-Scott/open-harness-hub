#!/usr/bin/env python3
"""scripts.check_structured_runtime_logging — proof: runtime logs are structured JSON with the canonical
correlation fields (tenant_id, run_id, step_id, processor_id/version, trace_id, correlation_id), use stable
event names, and never leak a raw secret.

CLI: python3 scripts/check_structured_runtime_logging.py --self-test
"""
from __future__ import annotations

import argparse
import json

from scripts.runtime.context import build_context
from scripts.runtime.envelopes import CommandEnvelope
from scripts.runtime.processor_harness import run_command
from scripts.runtime.processor_registry import default_registry

REQUIRED = ("timestamp", "level", "event", "tenant_id", "run_id", "trace_id", "correlation_id", "message", "fields")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    sink: list[str] = []
    ctx = build_context(tenant_id="acme", run_id="run-1", pipeline_id="cfpb_artifact_graph", pipeline_version="v1",
                        step_id="decompose")
    ctx.logger._sink = sink.append  # capture emitted lines
    rec = {"complaint_id": "C1", "product": "Credit card", "company": "Acme",
           "consumer_complaint_narrative": "Charged twice. No refund."}
    run_command(default_registry(), CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id="run-1",
                queue="q", pipeline_id="cfpb_artifact_graph", pipeline_version="v1", step_id="decompose",
                processor_id="decompose.cfpb_structured", processor_version="v1", payload={"records": [rec]}), ctx)

    check("logs were emitted", len(ctx.logger.records) > 0 and len(sink) == len(ctx.logger.records))
    check("every log line is valid JSON", all(isinstance(json.loads(s), dict) for s in sink))
    check("every record has the canonical correlation fields", all(all(k in r for k in REQUIRED) for r in ctx.logger.records))
    check("step records carry processor_id + processor_version",
          any(r["event"] == "pipeline.step.completed" and r["processor_id"] == "decompose.cfpb_structured"
              and r["processor_version"] == "v1" for r in ctx.logger.records))
    check("event names are stable/searchable (no ad-hoc 'done'/'ok')",
          {"pipeline.step.started", "pipeline.step.completed"} <= {r["event"] for r in ctx.logger.records})

    # secret redaction — fake key built at RUNTIME (no literal sk-… token in this source file)
    fake = "sk-" + "ABCDEF1234567890XYZ0"
    r = ctx.logger.info("processor.completed", message=f"using key {fake} now", api_key=fake, note="ok")
    blob = json.dumps(r)
    check("a secret in a log MESSAGE is redacted", fake not in blob and "REDACTED" in r["message"])
    check("a secret-named FIELD is redacted", r["fields"]["api_key"] == "***REDACTED***")
    check("no raw sk- key survives anywhere in the log record", fake not in blob)

    print(f"\n{'PASS — check_structured_runtime_logging: structured JSON logs with canonical correlation fields, stable event names, and secret redaction (no raw key ever logged).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: structured runtime logging + redaction.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
