# AIDevObserver Primitive-First Coding Benchmark

Last updated: 2026-07-01

This pack creates a 10,000-row corpus of realistic software/business build tasks for testing whether AIDevObserver's internal benchmark lab can prove primitive-first route assembly is faster, more reliable, and less token-wasteful than a generic AI coding flow.

Naming note: AIDevExplorer is not a branded public surface. The existing
`aidevexplorer` paths, script names, and JSON field names are a legacy/internal
namespace for this benchmark lab until a deliberate migration removes them.

The benchmark is candidate evidence, not truth:

```text
candidate=true
serves_truth=false
```

## Files

- `catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/tasks.jsonl`
  10,000 task rows compatible with the existing public-codegen use-case ingestion path.
- `catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/manifest.json`
  Corpus manifest with row, family, industry, and audience counts.
- `data/dev-intel/aidevexplorer_task_benchmarks/2026-06-30/suites.jsonl`
  100 benchmark suites, each containing 100 task IDs.
- `data/dev-intel/aidevexplorer_task_benchmarks/2026-06-30/manifest.json`
  Suite manifest.
- `data/dev-intel/aidevexplorer_task_benchmarks/2026-07-01/task_decompositions.jsonl`
  Task-level primitive-component decompositions for benchmark runs, one row per task.
- `data/dev-intel/aidevexplorer_task_benchmarks/2026-07-01/task_decompositions_manifest.json`
  Decomposition manifest with benchmark-lens coverage, component counts, and estimate-only token plan status.
- `data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards.jsonl`
  Compact AIDevObserver search cards generated from benchmark decompositions: one card per benchmark lens, task family, expected primitive, and expected primitive group.
- `data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards_manifest.json`
  Benchmark decomposition card manifest with source-row coverage and card-kind counts.
- `catalog/knowledge-packs/data/aidevexplorer-runtime-shape-tasks/tasks.jsonl`
  10,000 runtime-shape reuse rows: 1,000 core business tasks crossed with 10 deployable/callable surfaces.
- `catalog/knowledge-packs/data/aidevexplorer-runtime-shape-tasks/manifest.json`
  Runtime-shape corpus manifest with per-shape and per-primitive-kind counts.
- `data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards.jsonl`
  200 compact AIDevObserver reuse cards: 20 task families crossed with 10 runtime shapes.
- `data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards_manifest.json`
  Runtime-shape card manifest.
- `catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/families.jsonl`
  Primitive-kind family catalog for API, service, webhook, queue, cron, workflow, integration, database, DevOps, security, RAG/agent, UI, testing, and operations primitives.
- `data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards.jsonl`
  41 compact AIDevObserver reuse cards generated from the primitive-kind family catalog.
- `data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl`
  Source-backed Teleon primitive group cards for deterministic implementations with unit-test proof refs.
- `data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards_manifest.json`
  Source-backed card manifest; row counts are computed here rather than hand-typed in prose.
- `data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl`
  Earlier curated source-backed Teleon group cards loaded by AIDevObserver search.
- `data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_proof_bundles.jsonl`
  Database-shaped proof bundles for all loaded source-backed group records, one per primitive group.
- `data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_promotion_gates.jsonl`
  Promotion gate rows for each source-backed group; proofed candidates remain blocked pending owner review.

## What The Tasks Represent

The corpus is built from real recurring work patterns developers, freelancers, dev teams, and architects spend time on:

```text
CRUD APIs
webhook ingestion
tenant settings
admin dashboards
customer onboarding portals
frontend quality gates
CSV import pipelines
warehouse ELT
data quality incidents
docs RAG
knowledge-base migration
prompt/model evals
agent tool permissioning
CI hardening
deployment readiness
Kubernetes validation
security alert triage
dependency exceptions
invoice approval workflows
contract obligation tracking
```

Those patterns are crossed with 99 business contexts and 10 delivery variants, then capped at 10,000 rows.

## Row Shape

Each task row includes:

```text
id
title
audience
task_family
industry
business_area
team_context
intent
expected_template
expected_primitives
expected_primitive_groups
expected_deliverables
acceptance_criteria
observed_reinvention_patterns
common_pitfalls
aidevexplorer_eval_hooks
```

The important fields for the benchmark lab are `expected_primitives`,
`expected_primitive_groups`, and `aidevexplorer_eval_hooks`.

## Benchmark Decomposition Layer

Benchmark tasks should not remain opaque prompts. Each task should be split into logical primitive components so a runner can measure where tokens are spent:

```text
BenchmarkTaskIntent+TeamContext -> TaskAcceptanceContract
TaskAcceptanceContract+PrimitiveRegistry -> PrimitiveRouteCandidateSet
TaskAcceptanceContract+PrimitiveInput -> PrimitiveReceipt
PrimitiveRouteCandidateSet+Template -> AssembledPrimitiveRoute
AssembledPrimitiveRoute+AcceptanceCriteria -> BenchmarkProofReceipt
BaselineTrace+PrimitiveRouteTrace+ComponentAttribution -> TokenComparisonReceipt
```

The decomposition rows cover these benchmark lenses:

```text
agent_tooling_benchmark
api_application_benchmark
business_workflow_benchmark
ci_devops_benchmark
cloud_infra_benchmark
configuration_benchmark
content_migration_benchmark
data_import_benchmark
data_quality_benchmark
data_warehouse_benchmark
deployment_readiness_benchmark
event_integration_benchmark
frontend_quality_benchmark
llm_eval_benchmark
rag_retrieval_benchmark
security_governance_benchmark
security_triage_benchmark
ui_application_benchmark
```

The token comparison rows are intentionally estimate-only:

```text
estimate_only=true
actual_run_required=true
candidate=true
serves_truth=false
```

That keeps the planner honest: estimated savings can choose a benchmark batch, but only paired baseline and primitive-route traces can prove real token reduction.

Measured token proof uses a separate source-backed group:

```text
BaselineTrace+PrimitiveRouteTrace+TracePolicy -> BenchmarkTracePairEvaluationReceipt
```

That evaluator requires actual token counts, same-task trace pairs, component attribution, primitive usage, proof refs, successful runs, and the candidate boundary. It rejects estimated token traces as promotion evidence.

The decomposition-card build step makes those benchmark groups searchable without loading all 10,000 rows into AIDevObserver search. It emits compact candidate cards for:

```text
benchmark.decomposition.lens
benchmark.decomposition.task_family
benchmark.decomposition.expected_primitive
benchmark.decomposition.expected_group
```

The expected-primitive and expected-group cards are the important bridge from broad benchmark tasks to reusable capability search. They let AIDevObserver answer queries like "CSV import token proof", "RAG citation benchmark", "OpenAPI schema validation", or "queue worker idempotency" with a compact benchmark decomposition route instead of forcing the agent to inspect every task row.

These cards answer queries like:

```text
api benchmark decomposition token usage primitive components
csv import benchmark task family token comparison visible edges
file.read_csv_artifact record.identity_dedupe token comparison
rag retrieval benchmark decomposition proof token plan
grp:rag.docs_search@candidate retrieve.search_index citation coverage
api.validate_json_schema OpenAPI endpoint benchmark proof
queue.enqueue_job webhook idempotency token attribution
security triage benchmark primitive components token attribution
```

They stay candidate-only and point back to the full decomposition corpus. The search cards are route-selection aids, not measured lift evidence.

## Runtime-Shape Reuse Corpus

The runtime-shape corpus tests a different question than the broad task list:

```text
Can the AIDevObserver benchmark lab find one reusable core group edge and expose it through the right runtime wrapper without rebuilding the hidden logic?
```

It uses this matrix:

```text
1,000 base business tasks
x 10 runtime shapes
= 10,000 rows
```

The 10 runtime shapes are:

```text
py.fn
api.endpoint
microservice
webhook.handler
queue.consumer
cron.job
cli.command
workflow.automation
kubernetes.job
dashboard.report
```

Each row declares the deployable surface separately from the reusable core:

```text
primitive_kind
runtime_shape
input_edge
output_edge
core_group_edge
wrapper_edges
hidden_member_edges
adapter_mutators
effects
proof_requirements
```

For example, an API endpoint row can expose:

```text
HttpRequest[RawCsvArtifact+ImportPolicy] -> HttpResponse[ValidatedImportReceipt]
```

while preserving the core group edge:

```text
RawCsvArtifact+ImportPolicy -> ValidatedImportReceipt
```

The wrapper edges handle transport/auth/response shape; hidden member edges keep parse, validate, dedupe, persist, and receipt behavior attached to the core group.

Microservices are modeled as `service.group` rows, not as one giant function. The visible edge stays compact, while endpoint handlers, queues, persistence, retries, idempotency, observability, and audit receipts stay behind hidden member edges.

The runtime-shape task rows are intentionally not loaded directly into AIDevObserver search. A compact card build step aggregates them into one candidate reuse card per `(task_family, runtime_shape)`. Those 200 cards are loaded through the normal edge-foundry search path when the generated card file exists.

## Primitive-Kind Family Cards

Runtime shapes answer how a reusable edge is exposed. Primitive-kind family cards answer what kind of reusable thing is being searched for. This lane currently covers:

```text
api.endpoint
service.group
webhook.handler
queue.consumer
queue.producer
event.handler
cron.job
workflow.step
workflow.group
integration.connector
sdk.client
cli.command
shell.script
container.job
kubernetes.job
kubernetes.controller
terraform.module
github.action
db.migration
sql.view
sql.proc
etl.pipeline
elt.model
data.quality.rule
rag.pipeline
vector.indexer
llm.tool
policy.rule
auth.middleware
rate.limit.middleware
ui.component
ui.route
dashboard
alert.rule
runbook
security.compliance.workflow
test.fixture
contract.test
mock.server
graphql.resolver
grpc.method
```

Each primitive-kind card carries:

```text
visible input/output edge
hidden member edges
effects
runtime targets
adapter mutators
proof requirements
promotion blockers
common pitfalls
```

These cards are candidate-only family guides. They make AIDevObserver return the right reusable surface family for queries like database migrations, SaaS integration connectors, RAG pipelines, and agent-callable tools before any implementation is promoted.

## Source-Backed Group Cards

The source-backed card lane binds selected family cards to real deterministic implementations in `src/teleon/primitives/groups.py`. AIDevObserver currently loads source-backed group rows from both `curated_primitive_groups.jsonl` and `source_backed_primitive_group_cards.jsonl`.

Current source-backed group records include:

```text
grp:teleon.record_import.prepare@1
grp:teleon.exact_edge_route.compile@1
grp:teleon.route_to_group_card.collapse@1
grp:teleon.file.guarded_replace@1
grp:teleon.policy_api_request.evaluate@1
grp:teleon.tenant_settings.resolve@1
grp:teleon.deployment_readiness.evaluate@1
grp:teleon.prompt_model_outputs.evaluate@1
grp:teleon.database_migration.plan@1
grp:teleon.integration_sync.compile@1
grp:teleon.cited_answer.assemble@1
grp:teleon.webhook_event.verify@1
grp:teleon.queue_job.plan@1
grp:teleon.queue_payload_contract.plan@1
grp:teleon.queue_ack_policy.plan@1
grp:teleon.queue_poison_message_policy.plan@1
grp:teleon.queue_batch_consumer.plan@1
grp:teleon.queue_ordering_policy.plan@1
grp:teleon.worker_autoscale_policy.plan@1
grp:teleon.scheduled_job_tick.evaluate@1
grp:teleon.cli_command.compile@1
grp:teleon.kubernetes_job.plan@1
grp:teleon.dashboard_snapshot.build@1
grp:teleon.auth_middleware.evaluate@1
grp:teleon.rate_limit.evaluate@1
grp:teleon.tool_invocation.plan@1
grp:teleon.workflow_step.evaluate@1
grp:teleon.event_publish.plan@1
grp:teleon.domain_event_handler.evaluate@1
grp:teleon.sdk_client_request.plan@1
grp:teleon.terraform_module.plan@1
grp:teleon.github_action_workflow.plan@1
grp:teleon.data_quality_rule.evaluate@1
grp:teleon.vector_index_build.plan@1
grp:teleon.compliance_evidence.compile@1
grp:teleon.graphql_resolver.plan@1
grp:teleon.grpc_method.plan@1
grp:teleon.sql_view.plan@1
grp:teleon.sql_procedure.plan@1
grp:teleon.etl_pipeline.plan@1
grp:teleon.elt_model.plan@1
grp:teleon.alert_rule.evaluate@1
grp:teleon.runbook.compile@1
grp:teleon.incident_triage.plan@1
grp:teleon.oncall_escalation.plan@1
grp:teleon.status_page_update.plan@1
grp:teleon.maintenance_window.plan@1
grp:teleon.postmortem_actions.plan@1
grp:teleon.test_fixture.build@1
grp:teleon.mock_server.plan@1
grp:teleon.policy_rule.evaluate@1
grp:teleon.shell_script.plan@1
grp:teleon.kubernetes_controller.plan@1
grp:teleon.workflow_group.plan@1
grp:teleon.ui_component.plan@1
grp:teleon.ui_route.plan@1
grp:teleon.ui_api_binding.plan@1
grp:teleon.ui_form_validation.plan@1
grp:teleon.ui_table_state.plan@1
grp:teleon.dashboard_filter_contract.plan@1
grp:teleon.ui_accessibility_interaction.plan@1
grp:teleon.api_resource_group.plan@1
grp:teleon.microservice_bundle.plan@1
grp:teleon.service_boundary_contract.plan@1
grp:teleon.service_surface_inventory.plan@1
grp:teleon.service_data_ownership.plan@1
grp:teleon.service_startup_order.plan@1
grp:teleon.service_secret_binding.plan@1
grp:teleon.service_backpressure_policy.plan@1
grp:teleon.openapi_operations.extract@1
grp:teleon.asyncapi_operations.extract@1
grp:teleon.cloudevent.normalize@1
grp:teleon.serverless_function.plan@1
grp:teleon.observability_instrumentation.plan@1
grp:teleon.api_contract_test_suite.plan@1
grp:teleon.feature_flag.plan@1
grp:teleon.secret_rotation.plan@1
grp:teleon.agent_tool_schema.openapi_compile@1
grp:teleon.sdk_package.plan@1
grp:teleon.dockerfile.plan@1
grp:teleon.docker_compose_stack.plan@1
grp:teleon.helm_chart.plan@1
grp:teleon.rbac_policy_matrix.plan@1
grp:teleon.pii_redaction_policy.plan@1
grp:teleon.connector_auth_binding.plan@1
grp:teleon.idempotency_policy.plan@1
grp:teleon.pagination_contract.plan@1
grp:teleon.cors_security_headers.plan@1
grp:teleon.audit_log_policy.plan@1
grp:teleon.tenant_isolation.plan@1
grp:teleon.event_schema_compatibility.evaluate@1
grp:teleon.dead_letter_replay.plan@1
grp:teleon.cache_invalidation.plan@1
grp:teleon.document_chunking.plan@1
grp:teleon.retrieval_rerank_policy.plan@1
grp:teleon.citation_coverage.evaluate@1
grp:teleon.agent_tool_permission_matrix.plan@1
grp:teleon.model_routing_policy.plan@1
grp:teleon.prompt_regression_suite.plan@1
grp:teleon.memory_retention_policy.plan@1
grp:teleon.vector_index_freshness.evaluate@1
grp:teleon.canary_release.plan@1
grp:teleon.blue_green_deployment.plan@1
grp:teleon.slo_error_budget_policy.plan@1
grp:teleon.dependency_vulnerability_exception.evaluate@1
grp:teleon.secret_scan_findings.evaluate@1
grp:teleon.sbom_generation.plan@1
grp:teleon.license_compliance.plan@1
grp:teleon.backup_restore.plan@1
grp:teleon.circuit_breaker.plan@1
grp:teleon.retry_backoff_policy.plan@1
grp:teleon.timeout_budget.plan@1
grp:teleon.concurrency_limit.plan@1
grp:teleon.health_probe_contract.plan@1
grp:teleon.dependency_readiness.plan@1
grp:teleon.graceful_shutdown.plan@1
grp:teleon.chaos_experiment.plan@1
grp:teleon.openapi_compatibility.evaluate@1
grp:teleon.api_versioning_policy.plan@1
grp:teleon.api_deprecation_notice.plan@1
grp:teleon.error_envelope_contract.plan@1
grp:teleon.request_signing_policy.plan@1
grp:teleon.api_usage_plan.plan@1
grp:teleon.api_key_rotation.plan@1
grp:teleon.response_cache_policy.plan@1
grp:teleon.api_request_validation.plan@1
grp:teleon.api_auth_scope_matrix.plan@1
grp:teleon.api_async_job_endpoint.plan@1
grp:teleon.api_bulk_operation.plan@1
grp:teleon.api_operation_example_coverage.plan@1
grp:teleon.api_endpoint_telemetry.plan@1
grp:teleon.cdc_capture.plan@1
grp:teleon.stream_watermark.plan@1
grp:teleon.partition_strategy.plan@1
grp:teleon.data_lineage_contract.plan@1
grp:teleon.outbox_publication.plan@1
grp:teleon.inbox_deduplication.plan@1
grp:teleon.materialized_view_refresh.plan@1
grp:teleon.data_quarantine_policy.plan@1
grp:teleon.task_lease.plan@1
grp:teleon.worker_heartbeat.plan@1
grp:teleon.queue_visibility_timeout.plan@1
grp:teleon.cron_catchup_window.plan@1
grp:teleon.workflow_compensation.plan@1
grp:teleon.batch_checkpoint.plan@1
grp:teleon.run_artifact_manifest.plan@1
grp:teleon.execution_audit_trail.plan@1
grp:teleon.api_gateway_route.plan@1
grp:teleon.service_discovery_registration.plan@1
grp:teleon.service_dependency_contract.plan@1
grp:teleon.runtime_config_schema.plan@1
grp:teleon.environment_promotion.plan@1
grp:teleon.webhook_delivery_policy.plan@1
grp:teleon.consumer_group_offset.plan@1
grp:teleon.service_ownership_runbook.plan@1
grp:teleon.schema_drift_gate.plan@1
grp:teleon.migration_lock.plan@1
grp:teleon.data_retention_enforcement.plan@1
grp:teleon.tenant_data_boundary.plan@1
grp:teleon.backup_restore_drill.plan@1
grp:teleon.access_review_evidence.plan@1
grp:teleon.data_deletion_workflow.plan@1
grp:teleon.privileged_access_approval.plan@1
grp:teleon.connector_cursor_checkpoint.plan@1
grp:teleon.connector_field_mapping.plan@1
grp:teleon.external_identity_map.plan@1
grp:teleon.sync_conflict_resolution.plan@1
grp:teleon.connector_rate_limit_budget.plan@1
grp:teleon.webhook_replay_window.plan@1
grp:teleon.connector_error_quarantine.plan@1
grp:teleon.sync_reconciliation_report.plan@1
grp:teleon.primitive_candidate_intake.plan@1
grp:teleon.primitive_reuse_observation.plan@1
grp:teleon.primitive_proof_coverage_matrix.plan@1
grp:teleon.primitive_promotion_review.plan@1
grp:teleon.registry_publish_manifest.plan@1
grp:teleon.benchmark_run_arm.plan@1
grp:teleon.primitive_lift_comparison.plan@1
grp:teleon.token_savings_attribution.plan@1
grp:teleon.pitfall_avoidance_matrix.plan@1
grp:teleon.route_promotion_evidence_pack.plan@1
grp:teleon.runtime_shape_adapter.plan@1
grp:teleon.runtime_shape_adapter_matrix.plan@1
grp:teleon.openapi_endpoint_cards.compile@1
grp:teleon.asyncapi_event_cards.compile@1
grp:teleon.service_surface_cards.compile@1
grp:teleon.benchmark_primitive_decomposition.plan@1
grp:teleon.benchmark_route_token_usage.compare@1
grp:teleon.benchmark_trace_pairs.ingest@1
grp:teleon.benchmark_trace_pair.evaluate@1
grp:teleon.benchmark_route_promotion_candidate.evaluate@1
grp:teleon.primitive_consumer_readiness.evaluate@1
grp:teleon.primitive_registry_expansion_coverage.evaluate@1
grp:teleon.primitive_graph_runtime.plan@1
grp:teleon.container_runtime_cards.compile@1
grp:teleon.kubernetes_workload_cards.compile@1
grp:teleon.terraform_module_cards.compile@1
grp:teleon.ci_workflow_cards.compile@1
```

Each card carries a source function reference, hidden member edges, adapter mutators, proof requirements, and unit-test proof refs. They are still candidate cards:

```text
candidate=true
serves_truth=false
```

This lane is the bridge from abstract primitive-kind families to implementation-backed reuse. It lets AIDevObserver prefer source-backed groups for queries such as database migrations, integration syncs, and cited RAG answers while still requiring proof bundles and promotion review before any truth claim.

The registry-governance group records cover the primitive database lifecycle itself: candidate intake, runtime-shape reuse observation, proof coverage matrices, promotion review, and registry publish manifests. These are deliberately modeled as candidate-only primitives so AIDevObserver can explain why a route is searchable, proofed, or still blocked without converting a candidate row into truth.

The experiment-scorecard group records cover the benchmark loop itself: planning baseline and primitive-first run arms, comparing measured lift, attributing token savings to primitive reuse, proving common pitfalls were avoided, and packaging route-promotion evidence. These also stay candidate-only; a winning scorecard can feed promotion review, but it does not promote a primitive by itself.

The surface-card compiler group records cover the practical handoff from machine-readable software surfaces to AIDevObserver search cards: OpenAPI operations become candidate endpoint cards, AsyncAPI operations become candidate event cards, service-surface inventories become candidate microservice surface cards, and runtime-shape adapter matrices prove that only wrappers changed while the core group edge stayed reusable.

The benchmark decomposition group records make benchmark tasks more useful than pass/fail prompts. They split each task into logical primitive components, preserve each component's visible edge and proof requirements, and compare token usage of the primitive route against baseline or alternate routes with component-level attribution.

The benchmark trace-pair ingestion group is the bridge from raw run artifacts to measured evidence:

```text
BenchmarkRunArtifactSet+TraceIngestionPolicy -> BenchmarkTraceIngestionReceipt
```

It pairs baseline and primitive artifacts by task ID, checks trace refs, actual token counts, successful runs, primitive IDs, component attribution, proof refs, route reuse, and candidate/truth boundaries, then emits evaluator-ready trace pairs.

The benchmark trace-pair evaluator is the bridge from ingested trace pairs to scored evidence. It verifies same-task baseline and primitive traces, rejects estimate-only token counts, requires component attribution and proof refs, and emits a candidate receipt that can feed promotion review without setting `serves_truth=true`.

The benchmark route-promotion candidate evaluator aggregates repeated measured wins:

```text
BenchmarkTraceEvaluationSet+RoutePromotionPolicy -> BenchmarkRoutePromotionCandidateReceipt
```

It checks run count, task coverage, runtime-shape coverage, tool-consumer coverage, actual token-savings distribution, route reuse, proof refs, unresolved pitfalls, and candidate/truth boundaries. The current source-backed proof covers Codex, Claude Code, Kimi, GLM, and Gemma 4 as development-tool consumers, so the benchmark lab can ask whether a primitive route wins across tools rather than only in one agent trace. The result is promotion evidence, not automatic promotion.

The primitive consumer-readiness evaluator is the gate before graph assembly:

```text
PrimitiveEdgeCardSet+ConsumerSurfacePolicy -> PrimitiveConsumerReadinessReceipt
```

It checks whether candidate edge cards are compact, searchable, proof-aware, runtime-targeted, remixable, and safe for product/tool consumers. The current tool-consumer gates explicitly include Codex, Claude Code, Kimi, GLM, and Gemma 4, so the benchmark lab can test whether baseline coding tools get short reusable edge cards rather than full implementation dumps.

The primitive registry expansion coverage evaluator audits whether the primitive database actually covers the intended family/runtime surface:

```text
PrimitiveRegistrySnapshot+ExpansionCoveragePolicy -> PrimitiveRegistryExpansionCoverageReceipt
```

It checks required primitive kinds, runtime targets, source families, proof-bundle coverage, search-smoke coverage, and candidate/truth boundaries. This is the guard against vanity row growth: the benchmark lab should verify coverage for API endpoints, microservices, webhooks, queue workers, cron jobs, CLI commands, workflow automations, Kubernetes jobs, dashboards, RAG/agent tools, database migrations, DevOps/IaC, security/policy, and integration connectors before treating the benchmark registry as representative.

The primitive graph-runtime planner is the bridge from benchmark decomposition cards to executable route plans:

```text
UserIntent+PrimitiveEdgeCardSet+GraphPolicy -> PrimitiveGraphRuntimePlanReceipt
```

It consumes compact primitive cards rather than full source code, orders visible edges from `start_edge` to `goal_edge`, carries hidden member edges forward for drill-down, inserts runtime adapter mutators, preserves proof/effect/runtime-target requirements, and blocks unsafe routes that cross the candidate/truth boundary. That is the shape the benchmark lab should test: baseline agent reads and writes broadly, while the primitive-first run searches edge cards, orders a graph, proves it, and only expands implementation details where needed.

The deployment-surface compiler group records do the same for runtime artifacts: container services, Kubernetes workloads, Terraform resources, and CI workflows can be compiled into candidate registry cards with runtime safety checks, proof requirements, and promotion gates.

The current source-backed implementation coverage includes:

```text
api.endpoint
service.group
service.boundary_contract
service.surface_inventory
service.data_ownership
service.startup_order
service.secret_binding
service.backpressure_policy
container.job
contract.test
db.migration
integration.connector
rag.pipeline
webhook.handler
queue.consumer
queue.payload_contract
queue.ack_policy
queue.poison_message_policy
queue.batch_consumer
queue.ordering_policy
worker.autoscale_policy
cron.job
cli.command
kubernetes.job
dashboard
auth.middleware
rate.limit.middleware
llm.tool
workflow.step
queue.producer
event.handler
sdk.client
terraform.module
github.action
data.quality.rule
vector.indexer
security.compliance.workflow
graphql.resolver
grpc.method
sql.view
sql.proc
etl.pipeline
elt.model
alert.rule
runbook
ops.incident_triage
ops.oncall_escalation
ops.status_page_update
ops.maintenance_window
ops.postmortem_actions
test.fixture
mock.server
policy.rule
shell.script
kubernetes.controller
workflow.group
ui.component
ui.route
ui.api_binding
ui.form_validation
ui.table_state
dashboard.filter_contract
ui.accessibility_interaction
api.resource.group
api.openapi.extractor
event.asyncapi.extractor
event.cloudevents.normalizer
serverless.function
observability.instrumentation
feature.flag
security.secret.rotation
llm.tool.schema
sdk.package
container.dockerfile
container.compose
helm.chart
rbac.policy
privacy.pii.redaction
integration.connector.auth
api.idempotency.policy
api.pagination.contract
api.security_headers.cors
audit.log.policy
tenancy.isolation
event.schema.compatibility
queue.dead_letter_replay
cache.invalidation
rag.document_chunking
rag.retrieval_rerank
rag.citation_coverage
agent.tool_permission_matrix
llm.model_routing.policy
eval.prompt_regression
agent.memory_retention
vector.index_freshness
release.canary
release.blue_green
observability.slo_error_budget
security.dependency_exception
security.secret_scan
supply_chain.sbom
supply_chain.license_compliance
ops.backup_restore
resilience.circuit_breaker
resilience.retry_backoff
resilience.timeout_budget
resilience.concurrency_limit
resilience.health_probe
resilience.dependency_readiness
resilience.graceful_shutdown
resilience.chaos_experiment
api.openapi.compatibility
api.versioning_policy
api.deprecation_notice
api.error_envelope
api.request_signing
api.usage_plan
api.key_rotation
api.response_cache
api.request_validation
api.auth_scope_matrix
api.async_job_endpoint
api.bulk_operation
api.operation_example_coverage
api.endpoint_telemetry
data.cdc_capture
stream.watermark
data.partition_strategy
data.lineage_contract
event.outbox_publication
event.inbox_deduplication
data.materialized_view_refresh
data.quarantine_policy
worker.task_lease
worker.heartbeat
queue.visibility_timeout
cron.catchup_window
workflow.compensation
batch.checkpoint
artifact.run_manifest
audit.execution_trail
api.gateway_route
service.discovery_registration
service.dependency_contract
service.runtime_config_schema
release.environment_promotion
webhook.delivery_policy
event.consumer_group_offset
service.ownership_runbook
db.schema_drift_gate
db.migration_lock
data.retention_enforcement
tenancy.data_boundary
ops.backup_restore_drill
security.access_review_evidence
privacy.data_deletion_workflow
security.privileged_access_approval
integration.connector_cursor_checkpoint
integration.connector_field_mapping
integration.external_identity_map
integration.sync_conflict_resolution
integration.connector_rate_limit_budget
webhook.replay_window
integration.connector_error_quarantine
integration.sync_reconciliation_report
artifact.primitive_group
registry.primitive_candidate_intake
registry.primitive_reuse_observation
registry.primitive_proof_coverage
registry.primitive_promotion_review
registry.publish_manifest
benchmark.run_arm
benchmark.primitive_lift_comparison
benchmark.token_savings_attribution
benchmark.pitfall_avoidance_matrix
benchmark.route_promotion_evidence_pack
benchmark.route_promotion_candidate
runtime_shape.adapter
runtime_shape.adapter_matrix
registry.openapi_endpoint_card_compiler
registry.asyncapi_event_card_compiler
registry.service_surface_card_compiler
benchmark.primitive_decomposition
benchmark.route_token_usage
benchmark.trace_pair_ingestion
benchmark.trace_pair_evaluation
registry.container_runtime_card_compiler
registry.kubernetes_workload_card_compiler
registry.terraform_module_card_compiler
registry.ci_workflow_card_compiler
```

## Proof Bundle And Promotion Gate Lane

Source-backed cards get a companion proof lane:

```text
source-backed group record
-> proof_bundle row
-> promotion gate row
```

The proof bundle rows follow the `proof_bundle` table shape in `db/postgres/schema.sql`: `subject_id`, `subject_kind`, `proof_kind`, `status`, `proof_command`, artifact refs, input hashes, output hashes, and `proof_hash`.

The promotion gate rows are deliberately stricter than a passing test run. They record that unit tests passed, contracts and hidden member edges are declared, and the candidate boundary is preserved, but they still block promotion:

```text
promotion_gate_status=blocked_pending_owner_review
promotion_allowed=false
promotable_without_review=false
candidate=true
serves_truth=false
```

AIDevObserver search loads the source-backed group records as candidate reuse cards. The proof bundles and promotion gates are not search cards; they are registry evidence and metadata for promotion review. The proof lane should cover every source-backed group record currently loaded by AIDevObserver.

Compute the current proof lane count from the generated manifests:

```bash
python3 scripts/check_teleon_source_backed_primitive_group_cards.py
python3 scripts/check_teleon_source_backed_primitive_group_proof_bundles.py
```

When a source-backed group has matching evidence, AIDevObserver attaches compact proof metadata to the reuse card:

```text
proof_status=pass
promotion_gate_status=blocked_pending_owner_review
promotion_allowed=false
```

Proofed source-backed candidates get a small ranking boost so reusable, tested groups are preferred over less-specific generated rows. The boost is only search ranking; it does not promote the record or set `serves_truth=true`.

## Benchmark Loop

Run:

```bash
python3 scripts/generate_aidevexplorer_real_world_task_corpus.py
python3 scripts/check_aidevexplorer_real_world_task_corpus.py
python3 scripts/build_aidevexplorer_task_benchmark_suites.py --date 2026-06-30
python3 scripts/check_aidevexplorer_task_benchmark_suites.py --date 2026-06-30
python3 scripts/build_aidevexplorer_benchmark_task_decompositions.py --date 2026-07-01
python3 scripts/check_aidevexplorer_benchmark_task_decompositions.py --date 2026-07-01
python3 scripts/build_aidevexplorer_benchmark_decomposition_cards.py --date 2026-07-01
python3 scripts/check_aidevexplorer_benchmark_decomposition_cards.py
python3 scripts/generate_aidevexplorer_runtime_shape_task_corpus.py
python3 scripts/check_aidevexplorer_runtime_shape_task_corpus.py
python3 scripts/build_aidevexplorer_runtime_shape_primitive_cards.py
python3 scripts/check_aidevexplorer_runtime_shape_primitive_cards.py
python3 scripts/generate_aidevexplorer_primitive_kind_family_catalog.py
python3 scripts/check_aidevexplorer_primitive_kind_family_catalog.py
python3 scripts/build_aidevexplorer_primitive_kind_cards.py
python3 scripts/check_aidevexplorer_primitive_kind_cards.py
python3 -m unittest tests/unit/test_teleon_primitive_groups.py
python3 scripts/build_teleon_source_backed_primitive_group_cards.py
python3 scripts/check_teleon_source_backed_primitive_group_cards.py
python3 scripts/build_teleon_source_backed_primitive_group_proof_bundles.py
python3 scripts/check_teleon_source_backed_primitive_group_proof_bundles.py
python3 scripts/primitive_source_lifecycle.py --self-test
```

Then run each suite twice:

```text
baseline: generic AI coding agent without primitive search
candidate: AIDevObserver benchmark lab with primitive search and route assembly
```

For each task, collect:

```text
wall_clock_minutes
prompt_tokens
completion_tokens
files_touched
custom_code_lines
primitive_hits
primitive_groups_used
test_pass_rate
pitfalls_avoided
rework_loops
```

## Success Criteria

The AIDevObserver benchmark lab should not just finish tasks. It should avoid predictable waste:

```text
find a reusable primitive or primitive group before writing custom code
compose visible edges into a route
use hidden member edges only when needed
emit proof/tests/receipts
avoid known pitfalls listed on the task row
reduce prompt tokens by at least 30 percent
reduce wall time by at least 25 percent
reduce repeated repair loops
```

Benchmark results remain evidence only. They cannot promote a primitive or claim product truth without separate review.

## Foundry Ingestion

The task corpus keeps `source_kind=curated_public_codegen_use_case`, so the existing context foundry can ingest it directly:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --public-use-case-seeds catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/tasks.jsonl \
  --use-case-limit 100 \
  --skip-microsurface-atlas \
  --skip-source-discovery-search-seeds \
  --skip-multilingual-search-scopes \
  --skip-naics-search-scopes \
  --skip-business-operation-search-scopes
```

Use a small `--use-case-limit` for smoke tests and raise it for batch runs.
