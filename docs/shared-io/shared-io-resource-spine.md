# Shared I/O + Resource Spine

The portfolio-wide standard for how **every input, output, and shared resource** is shaped — so Teleon, Baltor,
and the open hubs (OpenContextHub / OpenSkillsHub / OpenToolsHub / OpenHarnessHub) never drift into incompatible
object shells, ID/status/provenance fields, or ad-hoc table/secret access.

> Map (single source): `architecture/shared_io_spine.json` · Resource taxonomy: `architecture/shared_resource_spine.json`
> Proof: `scripts/check_shared_io_resource_spine.py`

## Core rule

- **Every input/output is typed, scoped, versioned, traceable, policy-aware, receipt-backed.**
- **Every shared resource is referenced through `ResourceRef` / `ResourceBinding` / `DataResourceSpec` +
  `ResourceProvisionReceipt`** — never a raw table/bucket/path name, raw key, or hidden env assumption in
  business logic.

## What is shared vs separate

| Shared (one definition, imported) | Separate (never merged) |
|---|---|
| schemas, contracts, ports, templates, numeric codes, policies, this spine map, dashboard components | product **truth**, customer data, production databases, tenant secrets, private artifacts |

"Shared" means a shared **contract + pattern**, not one shared production database.

## Where it lives (reconciliation note)

The spine lives in **`schemas/`** (JSON contracts read by everyone) + **`src/teleon/`** (the shared-infra layer
Baltor consumes via the `Baltor → Teleon` dependency law). We deliberately did **not** create a new top-level
`shared-platform/` tree — that would fragment the repo and trip `file_layout_policy`. The existing canonical
shell (`templates/schema-objects/canonical_object_shell.json` + `src/teleon/templates/instantiator`) is the
ObjectShell; resource helpers are new in `src/teleon/resources/`.

## The 14 layers (most already existed — this slice ratifies + fills the gap)

| Layer | Status | Key contracts |
|---|---|---|
| object_shell | **ratified + ReceiptRef new** | `ObjectShell.v1` (formalizes the 14-section canonical shell), `ReceiptRef.v1` |
| command_work_io | exists (extend) | `CommandEnvelope.v1`, queue-message, worker-run, `CapabilityTask.v1` |
| event_io | exists | `EventEnvelope.v1` (CloudEvents 1.0), `context-event`, `EVENT_KINDS` single source |
| api_io | partial | `ErrorEnvelope.v1` (rest queued: Api{Request,Response}Envelope, Pagination, …) |
| artifact_payload_io | partial | `Receipt.v1`, `ContextPack.v1`, `ReceiptRef.v1` (queued: Artifact/PayloadRef, ResultEnvelope) |
| **resource_io** | **NEW (the gap)** | `ResourceRef`, `ResourceBinding`, `DataResourceSpec`, `SecretRef`, `KeyRef`, `ResourceProvisionReceipt` |
| inference_io | exists | `InferencePreference`, `ResolvedInferencePreference`, `ModelInvocationReceipt`, `FreeLimitedEndpoint` |
| sandbox_io | exists | `SandboxRunRequest/Result/Policy` |
| evaluation_promotion_io | partial | `promotion-decision` (queued: EvaluationScorecard, PathComparisonReport, RollbackPlan, HumanApprovalReceipt) |
| registry_object_io | exists | `context-artifact`, `tool`, `harness`, `rubric` (conform to ObjectShell over time) |
| telemetry_io | partial | `WorkerTelemetry.v1` (queued: TraceContext/TelemetryEvent/JsonLogRecord → OpenTelemetry mapping) |
| policy_io | queued | TenantScope, DataClassification, VisibilityPolicy, ResourceAccessPolicy |
| openapi_asyncapi | queued | `spec/openapi/*`, `spec/asyncapi/*` (generated from schemas) |

## Resource layer (the new piece)

`src/teleon/resources/resource_ref.py` builders + guards, branching on numeric codes from
`shared_resource_spine.json`:

- **Ownership modes**: `external_existing(100)`, `managed_persistent(200)`, `managed_ephemeral(300)`,
  `pipeline_temp(400)`, `tenant_dedicated(500)`.
- **Kinds**: relational_table, object_bucket, queue, vector_index, graph_store, sandbox_volume, temp_dataset,
  blob_object, analytics_table.
- **Guards (proven)**: no raw secret/DSN in a spec (use `secret_ref` / `key_ref`); temporary ⇒ `ttl_seconds`;
  persistent ⇒ `owner` + `retention_class`; non-local provider ⇒ `local_equivalent` (offline golden path);
  every spec carries a `logical_name` (physical handle lives in the `ResourceBinding`).

A worker never writes `CREATE TABLE random_name`; it calls
`validate_resource_spec(make_data_resource_spec(...))` and provisions through a binding, emitting a
`ResourceProvisionReceipt`.

## The clause (carried in every workflow prompt)

> **SHARED I/O + RESOURCE SPINE CLAUSE.** All portfolio objects and runtime boundaries use standardized typed
> I/O: ObjectShell, CommandEnvelope, EventEnvelope, Api{Request,Response}Envelope, ErrorEnvelope, ArtifactRef,
> ResourceRef, ReceiptRef, ModelInvocationReceipt, SandboxRunResult, EvaluationScorecard, PromotionDecision, +
> policy/visibility/scope objects. No product invents incompatible id/status/provenance/tenant/visibility/
> resource fields. No worker references raw tables, buckets, keys, providers, or cloud resources directly — it
> uses ResourceRef/ResourceBinding/DataResourceSpec + receipts. Templates generate shapes; harnesses prove
> outputs; Teleon runs capabilities; Baltor governs truth.

## Queued (see `prompts/shared-io-resource-spine.md`)

Command/work split (WorkItem/WorkerClaim/AckNack/DLQ/IdempotencyKey/OutboxEvent); CloudEventProjection; the API
envelope set + OpenAPI/AsyncAPI generation; ArtifactRef/PayloadRef/ResultEnvelope; the evaluation/promotion set;
telemetry → OpenTelemetry mapping; the policy/visibility set; a standalone redteam + full-stack proof; migrating
existing object families to explicitly conform to `ObjectShell.v1`.
