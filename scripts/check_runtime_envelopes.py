#!/usr/bin/env python3
"""scripts.check_runtime_envelopes — proof: the five contract envelopes construct, carry required fields,
content_hash/idempotency, and a correlation/causation chain.

CLI: python3 scripts/check_runtime_envelopes.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.envelopes import (ArtifactEnvelope, CommandEnvelope, ErrorEnvelope, EventEnvelope,
                                       ProcessorResult, content_hash)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cmd = CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id="run-1",
                          queue="q", step_id="decompose", processor_id="decompose.cfpb_structured",
                          processor_version="v1", payload={"records": []})
    check("CommandEnvelope gets a content-derived command_id + idempotency_key + correlation_id",
          cmd.command_id.startswith("cmd-") and cmd.idempotency_key and cmd.correlation_id == "run-1")
    check("CommandEnvelope schema_version is versioned", cmd.schema_version == "CommandEnvelope")

    evt = EventEnvelope(type="baltor.pipeline.step.completed", source="baltor.test",
                        subject="run-1/step/decompose", tenant_id="acme", run_id="run-1", causation_id=cmd.command_id,
                        data={"facts": 3})
    check("EventEnvelope is CloudEvents-shaped (specversion/id/source/type/time/datacontenttype/subject/data)",
          evt.specversion == "1.0" and evt.id.startswith("evt-") and evt.datacontenttype == "application/json" and "facts" in evt.data)
    check("correlation/causation chain links event→command", evt.causation_id == cmd.command_id and evt.correlation_id == "run-1")

    art = ArtifactEnvelope(artifact_id="run-1:atomic_fact:f1", tenant_id="acme", artifact_type="atomic_fact",
                           artifact_schema_version="AtomicFact", content_hash=content_hash({"x": 1}),
                           payload={"text": "t", "field": "company", "claim_status": "fact", "promotion_eligible": True},
                           lineage={"run_id": "run-1", "pipeline_id": "p", "pipeline_version": "v1",
                                    "processor_id": "decompose.cfpb_structured", "processor_version": "v1"},
                           governance={"claim_status": "fact", "promotion_eligible": True, "model_dependent": False},
                           security={"classification": "demo_public"})
    check("ArtifactEnvelope carries content_hash + lineage + governance + security",
          art.content_hash.startswith("sha256:") and art.lineage["run_id"] == "run-1"
          and art.governance["promotion_eligible"] is True and art.security["classification"])

    res = ProcessorResult.make_ok(run_id="run-1", step_id="decompose", processor_id="decompose.cfpb_structured",
                                  processor_version="v1", artifacts=[art], events=[evt], metrics={"n": 1})
    rd = res.to_dict()
    check("ProcessorResult serializes nested envelopes", rd["ok"] and rd["artifacts"][0]["artifact_id"] == art.artifact_id
          and rd["events"][0]["type"] == evt.type)

    err = ErrorEnvelope("schema_validation_failed", retryable=False, message="bad", run_id="run-1", step_id="decompose")
    err2 = ErrorEnvelope("transient", retryable=True, message="timeout")
    check("ErrorEnvelope classifies retryable vs permanent", err.retryable is False and err2.retryable is True and err.error_id.startswith("err-"))

    check("envelope ids are deterministic (content-derived, no clock/rng)",
          CommandEnvelope(command_type="x", tenant_id="t", run_id="r", queue="q").command_id
          == CommandEnvelope(command_type="x", tenant_id="t", run_id="r", queue="q").command_id)

    print(f"\n{'PASS — check_runtime_envelopes: all five envelopes construct with required fields, content-derived ids, and a correlation/causation chain.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: runtime envelope contracts.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
