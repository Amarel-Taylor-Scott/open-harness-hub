# /workflows /shared-io-resource-spine  (C-SHARED-IO-1)

> **STATUS (2026-06-06).** Slice 1 BUILT + proven (`scripts/check_shared_io_resource_spine.py`, flywheel-
> registered). Built: the spine map (`architecture/shared_io_spine.json`) ratifying the existing typed-I/O
> contracts into one named standard; `ObjectShell` (formalizes the canonical 14-section shell) + `ReceiptRef`;
> the **resource layer** (`ResourceRef/ResourceBinding/DataResourceSpec/SecretRef/KeyRef/ResourceProvisionReceipt`
> + `_repos/teleon/backend/src/teleon/resources/resource_ref.py` guards + `architecture/shared_resource_spine.json`); embedded redteam.
> Doc: `docs/shared-io/shared-io-resource-spine.md`.
>
> **RECONCILIATION (warranted by repo principle).** The spine lives in `schemas/` + `src/teleon` (the shared-infra
> layer Baltor consumes via Baltor→Teleon), NOT a new top-level `shared-platform/` tree (would fragment the repo +
> trip `file_layout_policy`). The existing canonical shell + envelopes are RATIFIED, not duplicated.
>
> **QUEUED:** everything below not marked built.

You are Claude Code running the SHARED I/O + RESOURCE SPINE workflow. Goal: a portfolio-wide standardized
input/output/resource layer used by Teleon, Baltor, the four open hubs, the Shared Template Registry, the Shared
Inference Gateway, and the Shared Sandbox Gateway.

**Do not:** create a second runtime · create a second durable ledger · create product-specific duplicate object
shells · let each hub invent its own id/status/provenance/visibility fields · replace existing working contracts
(discover + extend) · break the Baltor demo/flywheel.

**Core rule:** every input/output is typed, scoped, versioned, traceable, policy-aware, receipt-backed. Every
shared resource is referenced through ResourceRef/ResourceBinding/ResourceProvisionReceipt. No raw secrets, raw
table names, raw cloud resources, or hidden environment assumptions in business objects.

1. **DISCOVERY FIRST** → `.agent/shared-io-resource-spine-discovery.json` (done inline this slice: found
   envelopes/CommandEnvelope+EventEnvelope+ErrorEnvelope, canonical_object_shell, sandbox/*, inference/*,
   promotion-decision, EVENT_KINDS; resource layer was the gap).
2. **SHARED PLATFORM LOCATION** — reconciled to `schemas/{shared,io,resources,evaluation,policy,telemetry}` +
   `_repos/teleon/backend/src/teleon/{resources,...}` + `architecture/shared_*_spine.json` (NOT `shared-platform/`).
3. **UNIVERSAL OBJECT SHELL** — `schemas/shared/ObjectShell` ✓ (+ ObjectIdentity/Scope/Status/Visibility/
   Provenance/Lineage/Policy/Relationships/Receipts mixins QUEUED). Rule: major objects compose/conform; no
   incompatible id/status/visibility/provenance; control on numeric codes. Proof `check_shared_object_shell` (folded
   into the spine proof for now).
4. **COMMAND / WORK I/O** — `CommandEnvelope` ✓ exists; QUEUED: `WorkItem/WorkerClaim/AckNackReceipt/
   DeadLetterEntry/IdempotencyKey/OutboxEvent` → `scripts/check_shared_command_work_io.py`.
5. **EVENT I/O** — `EventEnvelope` ✓ (CloudEvents 1.0; correlation_id+causation_id); QUEUED `CloudEventProjection`
   → `check_shared_event_io.py`.
6. **API I/O** — `ErrorEnvelope` ✓; QUEUED `ApiRequestEnvelope/ApiResponseEnvelope/Pagination/FilterSpec/
   ProjectionRef/AuthScope` + `spec/openapi/shared-api-patterns.yaml` → `check_shared_api_io.py`.
7. **ARTIFACT / PAYLOAD I/O** — `Receipt`/`ContextPack` ✓, `ReceiptRef` ✓; QUEUED `ArtifactRef/PayloadRef/
   GeneratedArtifact/ResultEnvelope/OutputContractValidation` → `check_shared_artifact_io.py`.
8. **RESOURCE I/O** — ✓ BUILT: `ResourceRef/ResourceBinding/DataResourceSpec/ResourceProvisionReceipt/SecretRef/
   KeyRef`; QUEUED `TemporaryResourceSpec/PersistentResourceSpec` (folded into ownership for now), `ResourceProvisionPlan`.
   Ownership modes: external_existing/managed_persistent/managed_ephemeral/pipeline_temp/tenant_dedicated. Proof
   `check_shared_io_resource_spine.py` ✓ (will split to `check_shared_resource_io.py`).
9. **INFERENCE I/O** — `InferencePreference/ResolvedInferencePreference/ModelInvocationReceipt/FreeLimitedEndpoint`
   ✓; QUEUED `InferenceRequest/StructuredInferenceRequest/EmbeddingRequest/JudgeRequest/ModelRouteDecision`.
10. **SANDBOX I/O** — `SandboxRunRequest/Result/Policy` ✓; QUEUED `SandboxNetworkPolicy/SandboxFilesystemPolicy/
    SandboxSecretPolicy/SandboxReceipt/SandboxRedteamReport`.
11. **EVALUATION / PROMOTION I/O** — `promotion-decision` ✓; QUEUED `EvaluationRun/EvaluationScorecard/
    PathComparisonReport/RollbackPlan/BoundaryExpansionRequest/HumanApprovalReceipt`.
12. **REGISTRY OBJECT I/O** — ensure ContextArtifact/SkillArtifact/ToolArtifact/HarnessArtifact/TemplateArtifact/
    RepoSnapshot/RepoIntakeDecision/ProviderNode conform to ObjectShell (provenance + visibility/status; external ⇒
    source + why_ingested; discovery ≠ trust). QUEUED migration proof.
13. **TELEMETRY I/O** — `WorkerTelemetry` ✓; QUEUED `TraceContext/TelemetryEvent/MetricSample/JsonLogRecord/
    SpanLink` + `docs/telemetry/opentelemetry-mapping.md` (logs carry correlation/trace/span/tenant/object ids;
    no secrets).
14. **SECURITY / POLICY I/O** — QUEUED `TenantScope/DataClassification/VisibilityPolicy/DataPolicy/
    ToolExecutionPolicy/ModelDataPolicy/ResourceAccessPolicy/BoundaryPolicy` (tenant-private never flows to open
    surfaces; boundary expansion explicit).
15. **OPENAPI / ASYNCAPI GENERATION** — QUEUED `spec/openapi/contextiseverything-shared-api.yaml`,
    `spec/asyncapi/contextiseverything-events.yaml` (generated/validated from schemas; CloudEvents projection documented).
16. **REDTEAM** — embedded subset ✓ in the spine proof; QUEUED standalone `check_shared_io_resource_redteam.py`:
    object lacks tenant scope · lacks provenance · model call lacks actual-used receipt · sandbox output promoted as
    truth · raw secret in ResourceSpec · public OpenToolsHub tool lacks visibility policy · context artifact →
    CanonicalFact directly · candidate path promotes without scorecard · event lacks correlation_id · API returns
    nonstandard error · dashboard writes truth · registry object uses display string for control · resource creates
    cloud table without DataResourceSpec · customer-private context appears in open hub. All fail safely.
17. **DOCS** — `docs/shared-io/shared-io-resource-spine.md` ✓; QUEUED the per-layer docs.
18. **PROOFS** — slice proof ✓; QUEUED the per-layer split + `check_shared_io_resource_full_stack.py`. Regression:
    `demo_offline_full_baltor`, `check_no_direct_provider_bypass`, `check_baltor_full_stack_perfect`, `baltor_flywheel --once`.
19. **ACCEPTANCE** — A object_shell ✓ · B resource spine ✓ · C universal shell ✓ · D command/work (exists, extend) ·
    E event ✓ · F api (partial) · G artifact/payload (partial) · H ResourceRef/Binding/Receipt ✓ · I inference ✓ ·
    J sandbox ✓ · K eval/promotion (partial) · L registry conform (queued migration) · M telemetry→OTel (queued) ·
    N policy/security (queued) · O OpenAPI/AsyncAPI (queued) · P redteam (embedded ✓, standalone queued) · Q Baltor
    demo green ✓ · R flywheel green ✓.

## Recommended sequence (remaining)
1. (done) ObjectShell + ResourceRef/SecretRef/KeyRef + ReceiptRef.
2. CommandEnvelope companions (WorkerClaim/AckNack/DLQ/IdempotencyKey) wired to the durable runtime.
3. EventEnvelope CloudEvents projection + standalone event proof.
4. ModelRouteDecision + InferenceRequest (close the inference I/O set).
5. SandboxReceipt + sandbox sub-policies.
6. EvaluationScorecard + PromotionDecision companions + RollbackPlan/HumanApprovalReceipt.
7. OpenAPI + AsyncAPI generation.
8. Standalone redteam + dashboard cards + ObjectShell conformance migration.

## SHARED I/O + RESOURCE SPINE CLAUSE
All portfolio objects and runtime boundaries must use standardized typed inputs/outputs: ObjectShell,
CommandEnvelope, EventEnvelope, ApiRequest/ResponseEnvelope, ErrorEnvelope, ArtifactRef, ResourceRef, ReceiptRef,
ModelInvocationReceipt, SandboxRunResult, EvaluationScorecard, PromotionDecision, and policy/visibility/scope
objects. No product may invent incompatible id/status/provenance/tenant/visibility/resource fields. No worker may
reference raw tables, buckets, keys, providers, or cloud resources directly; it must use ResourceRef/
ResourceBinding/DataResourceSpec and receipts. Templates generate shapes, harnesses prove outputs, Teleon runs
capabilities, and Baltor governs truth.
