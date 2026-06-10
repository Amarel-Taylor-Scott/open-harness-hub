# Observability — section card

Section: `observability` (category: observability) · critical-path.

## Purpose

Every runtime action must be searchable and traceable without leaking secrets. Observability emits ONE
structured JSON log record per event, each carrying the canonical correlation fields (tenant_id, run_id,
step_id, processor_id/version, trace_id, correlation_id) and a STABLE, searchable `event` name
(`runtime.command.*`, `pipeline.step.*`, `artifact.created`, `schema.validation.failed`, …) — no ad-hoc
"done"/"ok" strings — and maps the same envelopes onto an OTel GenAI span tree for distributed tracing.

## Owner module

`scripts/runtime/logger.py` — `RuntimeLogger` (`info`, `warn`, `error`, `child`) with built-in redaction;
plus the `to_otel_span` seam that lifts events to OTel GenAI spans. Registered runtime owner `RuntimeLogger`
(`architecture/runtime_ownership.json#RuntimeLogger`).

## Contracts

Output: `log_event` (structured JSON) and `otel_span` (trace_id / span_id / parent_span_id + `gen_ai.*` /
`ctx.*` attributes; a `*.failed` event maps to ERROR status).

## Proof scripts

`scripts/check_structured_runtime_logging.py` and `scripts/check_otel_spans.py` — both registered in the
flywheel; the OTel proof runs over a REAL pipeline run, not a synthetic event.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_structured_runtime_logging.py --self-test
PYTHONPATH=. python3 scripts/check_otel_spans.py --self-test
```

## Limitations

Logs and spans are produced and shaped correctly, but the OTLP exporter / Langfuse sink is cataloged as a
candidate — spans are built and asserted in-process, not yet shipped to an external collector.

## Opportunities

Wire an OTLP exporter behind the span seam; route structured logs to a managed sink without changing call
sites.
