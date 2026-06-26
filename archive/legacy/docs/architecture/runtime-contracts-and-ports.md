# Runtime Contracts & Ports (C32)

The system has enough working behavior (durable execution, standalone worker, tenant-partitioned ingest,
atomic CFPB facts, two-process exactly-once proof). The next risk is **architectural drift**: each new
module inventing its own JSON shape, logging style, error behavior, and retry semantics. This pass adds a
thin-but-strict contract layer so modules can be swapped, versioned, and run through the same path without
freezing innovation — a module may change *internally*, but its *outside surfaces* stay stable.

```
SourceAdapter → ParserProvider → Decomposer → ArtifactLedger → VectorProvider
  → GraphBuilder → ConflictDetector → Reconciler → ContextPackBuilder → ReceiptRenderer
```
The names don't matter — the **contracts** do. Every module receives and emits the same envelope shapes.

## The five envelopes (`scripts/runtime/envelopes.py`)

| Envelope | Purpose | Schema |
|---|---|---|
| `CommandEnvelope.v1` | work to be done (durable queue payload) | `schemas/envelopes/CommandEnvelope.v1.schema.json` |
| `EventEnvelope.v1` | a fact about what happened — **CloudEvents 1.0** (specversion/id/source/type/time/datacontenttype/subject/data) | `…/EventEnvelope.v1` |
| `ArtifactEnvelope.v1` | a stored object (lineage + governance + security) | `…/ArtifactEnvelope.v1` |
| `ProcessorResult.v1` | what a processor returns (artifacts/events/commands/metrics) | `…/ProcessorResult.v1` |
| `ErrorEnvelope.v1` | a classified failure (retryable vs permanent) | `…/ErrorEnvelope.v1` |

Ids are content-derived and `created_at`/`time` are injected (a fixed clock in tests), so envelopes are
byte-stable. Canonical field names (`tenant_id`, `run_id`, `pipeline_id`, `processor_id`, `correlation_id`,
`causation_id`, `trace_id`, `content_hash`, `idempotency_key`, …) are enforced — no `customerId`/`job`/
`pipelineVersion` aliases past the boundary.

## The hard rule: schemas, not vibes

`scripts/runtime/schema_validator.py` is a minimal stdlib JSON-Schema validator (type / required /
properties / enum / additionalProperties / items — no `jsonschema` dependency). **No command, event,
artifact, processor result, or durable queue payload is accepted unless it validates against a versioned
schema.** A failure becomes a permanent `ErrorEnvelope(error_type="schema_validation_failed")`. The harness
validates the **raw** command before normalization, so a missing field can't be masked by a default.

## Ports + RuntimeContext (`scripts/runtime/ports.py`, `context.py`)

Processors reach the outside world **only** through `RuntimeContext` ports — `artifact_store`,
`object_store`, `vector_store`, `event_bus`, `durable_store`, `logger`, `secrets`, `llm_gateway`, `clock`.
No processor imports the admin server, the global `BUS`, or a vendor SDK. This is what makes modules
swappable and testable: in-memory adapters offline, SQLite/object-store/`context_events`/broker in
production — the processor doesn't change. (Ports are duck-typed Protocols; `DurableStore`,
`LocalObjectStore`, `context_events.EventBus`, the LLM gateway already satisfy them.)

## Processor + registry + harness

A `Processor` (`scripts/runtime/processor.py`) has one method:
`handle(command: CommandEnvelope, ctx: RuntimeContext) -> ProcessorResult`. The runner/harness only ever
calls that, so it never knows whether it is processing CFPB records, PDFs, LLM output, vectors, or edges.
Processors load **only** via `ProcessorRegistry` (`processor_registry.py`) by `processor_id@version`; an
unknown ref is a permanent `unavailable_processor` error; **runtime core imports no domain module directly**
(only `builtin_processors.py` adapts CFPB decomposition — it is *wrapped*, never rewritten).

`ProcessorHarness` (`processor_harness.py`) is the one wrapper every processor runs inside:
validate command → resolve processor → open a structured log span → `handle()` → validate the
ProcessorResult + every emitted ArtifactEnvelope (envelope **and** its declared artifact schema) → write
artifacts / publish events / enqueue follow-ups through the ports → classify any failure into an
ErrorEnvelope (exception → retryable; unknown processor / bad schema → permanent) → return a verdict the
durable worker uses to ack/nack. Processor authors write only business logic.

## Durable worker integration

`scripts/flywheel_worker.py` gained a `pipeline.run_step` branch that routes a `CommandEnvelope` through
the harness; ack/nack depends on the harness verdict (retryable → nack→retry→DLQ; permanent → recorded +
DLQ). The existing `tenant.doc` path and the two-process exactly-once proof are unchanged.

## Logging & tracing (`scripts/runtime/logger.py`)

Every log line is one JSON object with the canonical correlation fields (`tenant_id`, `run_id`, `step_id`,
`processor_id`/`version`, `trace_id`, `correlation_id`) and a **stable, searchable** `event` name
(`pipeline.step.started/completed`, `artifact.created`, `schema.validation.failed`, …) — no ad-hoc
`done`/`ok`/`processed 5`. Values are **redacted**, so a secret can never land in a log line.

## Standards map

`JSON Schema` → payload validation · `OpenAPI` (`docs/contracts/openapi.runtime.yaml`) → HTTP endpoints ·
`AsyncAPI` (`docs/contracts/asyncapi.runtime.yaml`) → queue/event contracts · `CloudEvents` → the event
envelope shape · OpenTelemetry-style attributes → log/trace naming. Local SQLite + `context_events` map to
broker/KEDA/Postgres later **without changing these contracts** — the dashboard stays a projection; the
durable store + event log are the source of truth.

## Proofs

`check_runtime_envelopes` · `check_runtime_schema_validation` · `check_processor_registry` ·
`check_processor_harness` · `check_cfpb_decompose_via_harness` · `check_worker_command_envelope` ·
`check_structured_runtime_logging` (+ the unchanged `check_durable_worker_parallel`). All registered in the
flywheel. The live `/api/runtime/*` HTTP endpoints are documented as the contract; wiring them into the
admin server is the deferred generalized-runtime pass (the contract layer they depend on is shipped).
