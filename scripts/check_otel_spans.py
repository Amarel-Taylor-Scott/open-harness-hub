#!/usr/bin/env python3
"""scripts.check_otel_spans — proof: envelope → OTel GenAI span tree, over a REAL pipeline run.

Unit: to_otel_span maps the envelope onto trace_id/span_id/parent_span_id + gen_ai.*/ctx.* attributes,
deterministically; a *.failed event → ERROR status. Integrated: run a real pipeline, lift its emitted
events to envelopes, project to OTel spans, and assert a valid span TREE — one trace_id per run, parent
links resolve, exactly one root, unique span_ids — i.e. the runtime is OTLP-exportable as-is.

CLI:
    python3 scripts/check_otel_spans.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile

from scripts.context_events import EventBus
from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.envelope import chain_events, make_envelope
from scripts.pipeline_runtime.otel import to_otel_span, to_otel_spans, validate_span_tree
from scripts.pipeline_runtime.processors import default_registry
from scripts.pipeline_runtime.runner import run_pipeline
from scripts.pipeline_runtime.specs import discover
from scripts.pipeline_runtime.store import PipelineLedger


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── unit ──
    root = make_envelope("pipeline.started", correlation_id="run-1", subject_id="run-1", engine="pipeline_runtime",
                         engine_version="v1", payload={"pipeline": "cfpb_structured_ingest@v1"})
    child = make_envelope("pipeline.completed", correlation_id="run-1", subject_id="run-1",
                          causation_id=root["event_id"], evidence={"output_hash": "sha256:z"})
    s_root, s_child = to_otel_span(root), to_otel_span(child)
    check("span has trace_id/span_id/name", s_root["trace_id"] == "run-1" and s_root["span_id"].startswith("span-") and s_root["name"] == "pipeline.started")
    check("root span has no parent", s_root["parent_span_id"] == "")
    check("child parent_span_id == root span_id (tree edge from causality)", s_child["parent_span_id"] == s_root["span_id"])
    check("gen_ai + ctx attributes present", s_root["attributes"]["gen_ai.system"] == "baltor" and s_root["attributes"]["ctx.pipeline"] == "cfpb_structured_ingest@v1")
    check("deterministic span_id", to_otel_span(root)["span_id"] == s_root["span_id"])
    fail_env = make_envelope("pipeline.failed", correlation_id="r", subject_id="r")
    check("*.failed event → ERROR status", to_otel_span(fail_env)["status"]["code"] == "STATUS_CODE_ERROR")
    check("valid two-span tree", validate_span_tree([s_root, s_child]) == [])

    # ── integrated: real run → span tree ──
    tmp = tempfile.mkdtemp(prefix="otel-proof-")
    store = DurableStore(tmp + "/d.db")
    ledger = PipelineLedger(store)
    bus = EventBus()
    seen: list[dict] = []
    bus.subscribe(seen.append)
    spec = discover()["cfpb_structured_ingest@v1"]
    res = run_pipeline(spec, tenant_id="acme", run_input={"fixture": True, "limit": 5, "source_id": "cfpb"},
                       ledger=ledger, registry=default_registry(), bus=bus)
    spans = to_otel_spans(chain_events(seen, pass_id="C38", engine_version="v1"))
    check("real run produced spans", len(spans) >= 3 and res["status"] == "done", str(len(spans)))
    check("real-run spans form a VALID span tree", validate_span_tree(spans) == [], str(validate_span_tree(spans)))
    check("all spans share ONE trace_id (the run id)", len({s["trace_id"] for s in spans}) == 1 and spans[0]["trace_id"] == res["run_id"])
    check("exactly one root span", sum(1 for s in spans if not s["parent_span_id"]) == 1)
    check("every span carries gen_ai.operation.name", all(s["attributes"].get("gen_ai.operation.name") for s in spans))
    check("a broken parent link is detected", validate_span_tree(spans + [{"trace_id": spans[0]["trace_id"], "span_id": "span-x", "parent_span_id": "span-nope"}]) != [])

    store.close()
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_otel_spans: envelopes project to an OTel GenAI span tree (one trace_id, resolvable parent links, single root, gen_ai.*+ctx.* attributes) over a REAL pipeline run; OTLP exporter is the swap.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: envelope → OTel GenAI span tree over a real run.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
