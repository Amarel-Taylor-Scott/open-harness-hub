#!/usr/bin/env python3
"""scripts.pipeline_runtime.otel — map the event envelope → OpenTelemetry GenAI-style spans (SEAM).

The C26 envelope already carries causality; this projects it onto the OTel data model so the runtime is
observable by ANY OTLP backend (Coralogix AI Center, etc.) without a vendor lock or new dependency. A
run's envelopes become a span TREE: `span_id` derived from `event_id`, `parent_span_id` from
`causation_id`, one `trace_id` per run; attributes use OTel GenAI (`gen_ai.*`) + our domain (`ctx.*`)
conventions. The actual OTLP exporter is the swap — this is the pure, testable mapping.
"""
from __future__ import annotations

from typing import Any

from scripts.foundry.scrapers import content_hash

SPAN_KIND_INTERNAL = "SPAN_KIND_INTERNAL"


def _span_id(event_id: str) -> str:
    return "span-" + content_hash(event_id)[:16] if event_id else ""


def to_otel_span(env: dict) -> dict:
    """Project one envelope onto an OTel-shaped span dict (deterministic; no clock/RNG)."""
    failed = str(env.get("event_type", "")).endswith(".failed")
    ev = env.get("evidence") or {}
    attributes: dict[str, Any] = {
        # OTel GenAI semantic conventions
        "gen_ai.system": "baltor",
        "gen_ai.operation.name": env.get("event_type"),
        # Baltor domain attributes
        "ctx.pipeline": (env.get("payload") or {}).get("pipeline"),
        "ctx.engine": env.get("engine"),
        "ctx.engine_version": env.get("engine_version"),
        "ctx.pass_id": env.get("pass_id"),
        "ctx.tick_id": env.get("tick_id"),
        "ctx.subject_type": env.get("subject_type"),
        "ctx.subject_id": env.get("subject_id"),
        "ctx.idempotency_key": env.get("idempotency_key"),
        "ctx.priority": env.get("priority"),
        "ctx.attempt": env.get("attempt"),
        "ctx.input_hash": ev.get("input_hash"),
        "ctx.output_hash": ev.get("output_hash"),
        "ctx.event_id": env.get("event_id"),
    }
    return {
        "trace_id": env.get("trace_id") or env.get("correlation_id"),
        "span_id": _span_id(env.get("event_id", "")),
        "parent_span_id": _span_id(env["causation_id"]) if env.get("causation_id") else "",
        "name": env.get("event_type"),
        "kind": SPAN_KIND_INTERNAL,
        "status": {"code": "STATUS_CODE_ERROR" if failed else "STATUS_CODE_OK"},
        "attributes": {k: v for k, v in attributes.items() if v is not None},
    }


def to_otel_spans(envelopes: list[dict]) -> list[dict]:
    return [to_otel_span(e) for e in envelopes]


def validate_span_tree(spans: list[dict]) -> list[str]:
    """A valid span tree: unique span_ids, every parent_span_id resolves, exactly one trace_id."""
    errs: list[str] = []
    ids = [s.get("span_id") for s in spans]
    if len(ids) != len(set(ids)):
        errs.append("duplicate span_id(s)")
    idset = set(ids)
    traces = {s.get("trace_id") for s in spans}
    if len(traces) > 1:
        errs.append(f"multiple trace_ids in one tree: {sorted(traces)}")
    roots = 0
    for s in spans:
        p = s.get("parent_span_id")
        if not p:
            roots += 1
        elif p not in idset:
            errs.append(f"span {s.get('span_id')} parent {p} resolves to no known span")
    if spans and roots != 1:
        errs.append(f"expected exactly 1 root span, found {roots}")
    return errs
