#!/usr/bin/env python3
"""scripts.check_invalid_command_envelope_safe_failure — proof (PART 0 of the Fact Watchtower): the
CommandEnvelope failure path is hard-fail-safe. A malformed command — including a NON-mapping payload
(None/str/list/int) that would crash `dict(command)` — never crashes the ProcessorHarness or the worker;
it produces a schema-valid, NON-retryable ErrorEnvelope with the identifiers salvaged from the raw payload
(command_id/run_id/step_id/processor_id/processor_version); and at the worker it dead-letters IMMEDIATELY
(no retry budget burned) rather than being reprocessed forever.

CLI: python3 scripts/check_invalid_command_envelope_safe_failure.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.durable_store import DurableStore
from scripts.flywheel_worker import work_once
from scripts.runtime.context import build_context
from scripts.runtime.envelopes import CommandEnvelope
from scripts.runtime.processor_harness import run_command
from scripts.runtime.processor_registry import default_registry
from scripts.runtime.schema_validator import validate_ref

REC = {"complaint_id": "C1", "product": "Credit card", "issue": "Billing", "company": "Acme",
       "consumer_complaint_narrative": "Charged twice. No refund."}
Q = "runtime.commands"


def _valid_command() -> CommandEnvelope:
    return CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id="run-1", queue=Q,
                           pipeline_id="cfpb_artifact_graph", pipeline_version="v1", step_id="decompose",
                           processor_id="decompose.cfpb_structured", processor_version="v1",
                           payload={"records": [REC]})


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = default_registry()
    ctx = build_context(tenant_id="t", run_id="r", step_id="s")  # FixedClock → deterministic, offline

    # 1) malformed payloads of every shape fail SAFELY (no crash) with a schema-valid permanent ErrorEnvelope
    crashed = []
    bad_shapes = {"None": None, "str": "garbage", "list": [1, 2, 3], "int": 42, "empty_dict": {}}
    all_schema_valid = True
    for label, payload in bad_shapes.items():
        try:
            out = run_command(reg, payload, ctx)
        except Exception as e:  # noqa: BLE001 — ANY exception here is the bug we are proving cannot happen
            crashed.append(f"{label}:{type(e).__name__}"); continue
        if not (out.get("ok") is False and out.get("status") == "failed"):
            crashed.append(f"{label}:not-failed"); continue
        err = out["error"]
        if not (err["error_type"] == "schema_validation_failed" and err["retryable"] is False
                and err["failed_schema"] == "CommandEnvelope.v1"):
            crashed.append(f"{label}:bad-error-fields")
        if validate_ref(err, "envelopes/ErrorEnvelope.v1") != []:
            all_schema_valid = False
    check("malformed payloads (None/str/list/int/empty) never crash the harness", crashed == [], str(crashed))
    check("each failure is a NON-retryable schema_validation_failed on CommandEnvelope.v1", crashed == [])
    check("the emitted ErrorEnvelope is itself schema-valid (command_id field accepted)", all_schema_valid)

    # 2) identifiers are salvaged from the raw payload when present (traceable even though cmd was never built)
    bad = {"command_type": "pipeline.run_step", "command_id": "cmd-9", "run_id": "run-9", "step_id": "step-9",
           "processor_id": "proc-9", "processor_version": "v9", "tenant_id": "t", "queue": Q}  # missing required fields
    out = run_command(reg, bad, ctx)
    err = out["error"]
    check("ErrorEnvelope copies command_id/run_id/step_id/processor_id/processor_version from raw",
          (err["command_id"], err["run_id"], err["step_id"], err["processor_id"], err["processor_version"])
          == ("cmd-9", "run-9", "step-9", "proc-9", "v9"), str(err))

    # 3) the happy path is unbroken — a valid CommandEnvelope still passes validation and runs
    good = run_command(reg, _valid_command(), ctx)
    check("a valid CommandEnvelope still validates + runs (no regression)", good.get("ok") is True, str(good.get("error")))

    # 4) at the WORKER: an invalid command dead-letters IMMEDIATELY (default retry budget, not exhausted)
    store = DurableStore(":memory:")
    bad_cmd = dict(_valid_command().to_dict()); bad_cmd.pop("run_id"); bad_cmd["command_id"] = "cmd-bad"
    store.enqueue(Q, bad_cmd, idempotency_key="bad-perm")  # DEFAULT max_attempts (5)
    r = work_once(store, Q, worker_id="w1", now=2000)
    check("worker does not crash on an invalid command (returns a verdict)", isinstance(r, dict) and r.get("ok") is False, str(r))
    check("invalid command is flagged permanent + dead-lettered on the FIRST attempt (not reprocessed forever)",
          r.get("permanent") is True and store.stats(Q).get("dead", 0) == 1 and store.stats(Q).get("queued", 0) == 0,
          str(store.stats(Q)))
    evs = store.recent_events(limit=200)
    check("a processor.failed/ErrorEnvelope event was recorded durably", any(e.get("kind") == "processor.failed" for e in evs))

    # contrast: a valid command on the same worker still ACKs
    vc = _valid_command()
    store.enqueue(Q, vc.to_dict(), idempotency_key=vc.idempotency_key)
    r2 = work_once(store, Q, worker_id="w1", now=2001)
    check("a valid command on the same worker still ACKs (done)", bool(r2 and r2.get("ok")) and store.stats(Q).get("done", 0) == 1, str(store.stats(Q)))
    store.close()

    print(f"\n{'PASS — check_invalid_command_envelope_safe_failure: malformed commands fail safely (no crash), produce a schema-valid non-retryable ErrorEnvelope with salvaged ids, and dead-letter immediately at the worker.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: CommandEnvelope invalid path is hard-fail-safe.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
