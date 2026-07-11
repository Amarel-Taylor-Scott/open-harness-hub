# Claude Code Web Handoff: Primitive Foundry, Route Compiler, and Remix System

Use this document as a paste-ready brief for Claude Code on the web. The goal is to help another coding agent continue improving the primitive system without losing the core architecture, record formats, ranking logic, and operating rules.

## 0. Mission

Build a large, useful, evidence-backed primitive bank for AI software development.

The system should not be one primitive generator, one search method, one compiler, or one model. It should be a strategy tournament:

```text
many source adapters
+ many primitive generators
+ many search/ranking paths
+ many remixers/mutators
+ many compilers
+ many proof systems
+ many benchmark suites
+ telemetry receipts
= promoted primitive routes and reusable primitive groups
```

The target operating rate is at least:

```text
1,000 useful primitive candidates per day
```

The longer-term target is:

```text
hundreds of thousands to millions of primitive ideas, implemented code primitive records, primitive templates, primitive groups, route portfolios, mutators, wrappers, proof plans, benchmarks, and promotion receipts
```

Do not confuse seed ideas with verified primitives. Seed ideas are useful, but they are not truth. Every unproven generated row remains:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

## 1. Repository Context

The repo is an AI Done Right / OpenHubForAI catalog and primitive-system workspace.

Always start by reading:

```text
README.md
taxonomy/SPEC.md
AGENTS.md
docs/codex/no-magic-values.md
```

Important existing concepts:

```text
OpenHubForAI: open registry and schema layer.
Teleon: purpose-driven, eval-gated, self-adaptive compute runtime.
Baltor: managed, verified, provable context powered by Teleon.
AIDevObserver: reviews and improves AI coding-agent usage.
```

The catalog already has schema-validated components, processors, harnesses, pipelines, rule packs, tools, adapters, benchmarks, and foundry logic. The primitive work should extend that system rather than create a disconnected one.

## 2. Current High-Value Local Artifacts

Implemented-code primitive miner:

```text
scripts/mine_implemented_code_primitives.py
```

Current generated daily implemented primitive artifact:

```text
data/dev-intel/implemented_code_primitives/daily_20260702_2k/implemented_code_primitives.jsonl
data/dev-intel/implemented_code_primitives/daily_20260702_2k/manifest.json
data/dev-intel/primitive_factory/progress/daily_20260702_2k_implemented_code_primitives_progress.md
```

Verified current daily result:

```text
rows: 2,000
unique primitive_ids: 2,000
unique dedupe_keys: 2,000
snippet_compile_pass: 2,000
snippet_compile_fail: 0
functions: 1,700
classes: 300
verification_level: L4_source_ast_snippet_compiled
```

This is a reliable non-LLM production lane for generating real source-backed primitive records. It mines Python functions/classes, extracts signatures, source snippets, source spans, code hashes, input/output edges, proof requirements, and candidate metadata.

Run pattern:

```bash
python3 scripts/mine_implemented_code_primitives.py \
  --source-root src/teleon \
  --source-root scripts \
  --source-root /tmp/claude-code-online-repo/primitives \
  --limit 1000 \
  --run-id implemented_code_primitives_daily_YYYYMMDD_1k
```

Use `--offset 1000`, `--offset 2000`, etc. for additional batches. Keep batch manifests.

## 3. The Core Primitive Rule

The LLM should see the smallest useful contract first:

```text
visible input edge
+ visible output edge
+ blackbox behavior
+ effects
+ proof status
+ source/provenance summary
```

Only drill into hidden member edges, source snippets, full docs, or full code when the compact contract is insufficient.

This is the core context-compression rule.

## 4. Primitive Record Families

The primitive bank should contain many related record types, not only functions.

```text
PrimitiveCandidate
ImplementedCodePrimitiveCandidate
PrimitiveGroup
CapabilityCard
ProblemSolutionCard
PrimitiveOverlay
SourceAdapter
RuntimeWrapper
ProofAdapter
BenchmarkAdapter
Mutator
RouteCandidate
RoutePortfolio
PlanDelta
PlanLock
ExecutionReceipt
ProofReceipt
PromotionEvidence
NegativeMemory
StrategyGenome
RunTrace
Scorecard
CoOccurrenceEdge
DecompositionMemory
CacheReceipt
RegretRecord
```

## 5. Required Primitive Card Shape

Every primitive candidate should include at least:

```json
{
  "primitive_id": "prim:domain.capability.variant@1",
  "record_type": "primitive_candidate",
  "kind": "primitive",
  "family": "domain.capability",
  "title": "Human-readable title",
  "input_edge": "InputArtifact+Policy+Context",
  "output_edge": "OutputArtifact+Receipt",
  "blackbox": {
    "does": "What it does without implementation detail.",
    "llm_context_policy": "show_edge_first; drilldown_on_contract_or_proof_need"
  },
  "effects": [
    "file_read_optional",
    "network_read_optional",
    "artifact_write"
  ],
  "runtime_targets": [
    "python_function",
    "api_endpoint",
    "mcp_tool",
    "queue_worker"
  ],
  "source_refs": [],
  "proof_requirements": [
    "schema_validation",
    "fixture_behavior_test",
    "effect_audit"
  ],
  "problem_solution": {
    "problem": "The recurring problem this primitive solves.",
    "why_it_matters": "Why repeated agents should not rediscover this.",
    "solution": "The reusable capability or route.",
    "common_inputs": [],
    "common_outputs": [],
    "common_failures": [],
    "success_signals": []
  },
  "ranking": {
    "source_authority": 0.0,
    "proof_strength": 0.0,
    "reuse_potential": 0.0,
    "risk": 0.0
  },
  "candidate": true,
  "serves_truth": false
}
```

## 6. Implemented Code Primitive Shape

Source-backed code objects should use this richer shape:

```json
{
  "record_type": "implemented_code_primitive_candidate",
  "primitive_id": "impl:python.module.qualname.line24-8149c954@source",
  "code_object_id": "module.qualname",
  "title": "call function_name",
  "kind": "implemented_code_primitive",
  "code_kind": "function",
  "language": "python",
  "source_path": "src/teleon/example.py",
  "source_root": "src/teleon",
  "source_span": {
    "start_line": 24,
    "end_line": 67
  },
  "module": "module",
  "qualname": "function_name",
  "signature": "def function_name(a: str) -> dict",
  "parameters": ["a"],
  "return_annotation": "dict",
  "decorators": [],
  "docstring": "Short behavior summary.",
  "input_edge": "PythonFunction[module.function_name]+InvocationPolicy+SourceContext",
  "output_edge": "PythonFunctionReceipt+dict",
  "blackbox": "Short behavior summary.",
  "contract": {
    "problem": "Reuse source-backed Python function without asking a model to recreate it.",
    "summary": "Wraps implemented Python function as a candidate primitive.",
    "input": "PythonFunction[module.function_name]+InvocationPolicy+SourceContext",
    "output": "PythonFunctionReceipt+dict",
    "errors": "import_side_effect; missing_dependency; behavior_not_fixture_verified; unsafe_runtime_effect"
  },
  "edge_contract": {
    "input_edge_description": "Call-site payload for the signature plus execution policy and source context.",
    "output_edge_description": "Receipt and return value for the code object.",
    "preconditions": "Module source parses and snippet compiles.",
    "postconditions": "Source span, code hash, signature, and promotion blockers are recorded.",
    "failure_modes": "signature_mismatch; import_error; runtime_exception; missing_fixture; side_effect_not_declared",
    "composition_notes": "Generated by deterministic AST source mining from an implemented Python module."
  },
  "runtime_targets": ["python_import", "python_function"],
  "effects": ["unknown_runtime_effects_need_audit"],
  "proof_requirements": [
    "module_ast_parse",
    "snippet_compile",
    "import_smoke_test",
    "fixture_behavior_test",
    "effect_audit",
    "dependency_review"
  ],
  "promotion_blockers": [
    "import_smoke_not_run",
    "behavior_fixture_missing",
    "effects_not_audited",
    "source_license_review_needed"
  ],
  "validation": {
    "module_ast_parse_ok": true,
    "snippet_compile_ok": true,
    "snippet_compile_error": "",
    "source_span_present": true,
    "signature_extracted": true,
    "implementation_backed": true
  },
  "code": "def function_name(a: str) -> dict:\n    ...",
  "code_sha256": "sha256:...",
  "dedupe_key": "sha256-like-short-key",
  "rank_features": {
    "source_priority_score": 0,
    "has_docstring": true,
    "is_public": true,
    "parameter_count": 1
  },
  "generation_path": "deterministic_ast_source_mining",
  "verification_level": "L4_source_ast_snippet_compiled",
  "candidate": true,
  "serves_truth": false
}
```

## 7. Problem-Solution Is First-Class

Do not store only function descriptions. Store the recurring problem and the solved pattern.

Every primitive and primitive group should eventually have:

```json
{
  "problem_solution": {
    "problem_id": "problem:record_import.identity_dedupe@1",
    "problem": "Agents repeatedly need to import records and avoid duplicate entities.",
    "context": "Appears in CRM imports, customer trackers, vendor merges, patient identity, support tickets, and product catalogs.",
    "naive_agent_failure": "Rebuilds ad hoc merge code, silently drops fields, or creates duplicate records.",
    "solution": "Parse records, normalize fields, resolve identity, produce mutation plan, require audit receipt.",
    "core_components": [
      "schema_validate",
      "field_alias_resolve",
      "identity_rule_apply",
      "dedupe_cluster",
      "mutation_plan_emit",
      "audit_receipt_emit"
    ],
    "success_criteria": [
      "no_silent_field_drop",
      "duplicate_rate_reduced",
      "conflict_receipts_written",
      "idempotent_retry_safe"
    ],
    "known_pitfalls": [
      "email-only identity is unsafe",
      "phone normalization varies by region",
      "source_system+source_record_id must be preserved"
    ]
  }
}
```

This makes primitives reusable by intent, not only by symbol name.

## 8. Primitive Groups

Primitive groups hide a route behind a compact visible contract.

```json
{
  "primitive_id": "grp:customer.record_import.audit_safe@1",
  "record_type": "primitive_group",
  "kind": "artifact.primitive_group",
  "title": "Audit-safe customer record import",
  "input_edge": "RawCustomerRecordBatch+ImportPolicy+TargetSystem",
  "output_edge": "PreparedCustomerImport+ImportReceipt",
  "blackbox": {
    "does": "Parses, validates, normalizes, dedupes, and prepares customer records for import with audit evidence."
  },
  "group_contract": {
    "visible_input_edge": "RawCustomerRecordBatch+ImportPolicy+TargetSystem",
    "visible_output_edge": "PreparedCustomerImport+ImportReceipt",
    "hidden_member_edges": [
      "RawCustomerRecordBatch -> ParsedRecordBatch",
      "ParsedRecordBatch -> ValidatedRecordBatch",
      "ValidatedRecordBatch -> NormalizedCustomerBatch",
      "NormalizedCustomerBatch -> DedupedCustomerBatch",
      "DedupedCustomerBatch -> PreparedCustomerImport",
      "PreparedCustomerImport -> ImportReceipt"
    ]
  },
  "mutators": [
    "schema_validator_inserter",
    "field_alias_resolve",
    "idempotency_wrapper",
    "audit_receipt_wrapper"
  ],
  "proof_requirements": [
    "csv_fixture_test",
    "schema_contract_test",
    "identity_dedupe_fixture",
    "idempotency_test",
    "audit_receipt_schema_test"
  ],
  "candidate": true,
  "serves_truth": false
}
```

Groups are promoted when a route repeatedly succeeds, not because an LLM invented a plausible name.

## 9. Specialization Overlays

Do not create every Cartesian product as a full primitive. Compose overlays.

```text
base capability
+ algorithm/data-structure overlay
+ schema overlay
+ storage/runtime overlay
+ platform/API overlay
+ industry overlay
+ country/jurisdiction overlay
+ role/workflow overlay
+ proof/benchmark overlay
= resolved specialized primitive
```

Example:

```text
base: external_object_sync
+ schema: ShopifyOrder
+ canonical object: Order
+ industry: retail_ecommerce
+ target: QuickBooksInvoice
+ proof: money_reconciliation
+ runtime: queue_worker
= ShopifyOrderBatch+QuickBooksPolicy -> InvoiceSyncReceipt
```

Overlay record:

```json
{
  "overlay_id": "overlay:shopify.order@2026-07",
  "applies_to": "grp:base.external_object_sync@1",
  "platform": "shopify",
  "business_object": "order",
  "input_schema_ref": "ShopifyAdminGraphQL.Order",
  "field_map": {
    "order_id": "id",
    "customer_id": "customer.id",
    "line_items": "lineItems.nodes"
  },
  "auth_scopes": ["read_orders"],
  "proof_fixtures": [
    "shopify_order_minimal",
    "shopify_order_with_discount",
    "shopify_order_with_refund"
  ],
  "candidate": true,
  "serves_truth": false
}
```

## 10. Runtime Wrapper Primitives

The same core primitive should lower into different runtime shapes:

```text
python function
TypeScript function
FastAPI endpoint
GraphQL resolver
gRPC method
MCP tool
CLI command
queue worker
cron job
webhook handler
workflow step
Airflow task
Temporal activity
Dagster asset
Prefect flow
Argo workflow
Kubernetes job
cloud function
GitHub Action
Terraform module
Helm chart
browser automation script
dashboard widget
```

Wrapper record:

```json
{
  "primitive_id": "wrap:fastapi.endpoint@1",
  "kind": "runtime.wrapper",
  "input_edge": "CoreEdge+HttpPolicy",
  "output_edge": "OpenApiEndpointArtifact+WrapperReceipt",
  "effects": ["artifact_write", "network_bind_optional"],
  "proof_requirements": [
    "openapi_schema_validation",
    "request_response_contract_test",
    "error_envelope_test"
  ],
  "candidate": true,
  "serves_truth": false
}
```

## 11. Mutators and Remixers

Mutators are deterministic or bounded transformation operators that let near-matches compose safely.

### Deterministic Mutators

Use when behavior is fully mechanical:

```text
field_rename
field_project
field_default_insert
field_alias_resolve
type_cast
schema_validator_inserter
json_schema_enforcer
input_envelope_wrapper
output_receipt_wrapper
map_sequence
filter_sequence
batch_chunker
pagination_expander
retry_wrapper
timeout_wrapper
cache_wrapper
idempotency_wrapper
audit_receipt_wrapper
artifact_materialize
api_endpoint_wrapper
queue_worker_wrapper
cloud_function_wrapper
kubernetes_job_wrapper
route_to_group_card
```

### Genetic Mutators

Use in experiment mode to explore variants. Keep them reproducible.

```text
swap_retriever
swap_reranker
adjust_top_k
adjust_candidate_bundle_size
change_context_ladder
swap_planner_model
swap_lora_adapter
insert_mutator
remove_mutator
reorder_route_step
change_proof_order
change_cache_granularity
increase_or_reduce_source_fallback
temperature_mutation
beam_width_mutation
```

Every genetic mutation needs:

```json
{
  "sprout_id": "sprout:route.v43.to.v44",
  "parent_strategy_id": "strategy:route.v43",
  "mutation_operator": "swap_reranker",
  "changed_parameters": {
    "from": "ranker:crossencoder@5",
    "to": "ranker:local-bge@2"
  },
  "random_seed": 12345,
  "hypothesis": "Reduce cost while preserving route recall.",
  "safety_level": "shadow_only",
  "budget": {
    "max_tasks": 200,
    "max_cost_usd": 20
  },
  "promotion_metric": {
    "route_recall_at_10_min": 0.95,
    "proof_success_drop_max": 0.02,
    "cost_reduction_min": 0.5
  }
}
```

### Deterministic Remix

Use this path first when exact edges or mechanical adapters are available:

```text
RequestedEdge
-> CandidateBundle
-> ContractDiff
-> MutatorPlan
-> RouteCandidate
-> PlanLock
-> ProofReceipt
```

### Hybrid Remix

Use deterministic search plus bounded model selection:

```text
CandidateBundle
+ compact primitive cards
+ allowed mutators
+ proof policy
-> LLM PlanDelta
-> deterministic compiler validates everything
-> PlanLock
```

The model proposes. The compiler decides.

### LLM Remix

Use only for missing edges, new glue, or unclear decomposition. One model call should produce one primitive or one PlanDelta, not a giant batch.

Rules:

```text
1 call = 1 primitive, 1 route, or 1 repair.
No bulk generation inside one prompt for promoted records.
Model output remains candidate=true, serves_truth=false.
Run deterministic validation after every call.
Checkpoint every accepted record.
```

## 12. Search Paths

Do not rely on one retrieval method. Use a search portfolio.

```text
exact edge search
type-compatible search
schema similarity search
lexical BM25 search
dense embedding search
hybrid lexical/vector search
graph route search
known-chain search
benchmark-demand search
source-ref search
negative-memory search
receipt-boosted reranking
co-occurrence boosted reranking
cost-aware search
freshness-aware search
context-depth-aware search
```

Search returns a `CandidateBundle`, not a single answer.

```json
{
  "candidate_bundle_id": "cb:customer_import_001",
  "query_edge": "CustomerCsv+CrmTarget+AuditPolicy -> CrmImportReceipt",
  "retrieval_paths": [
    "edge_exact",
    "schema_similarity",
    "receipt_boosted_hybrid"
  ],
  "candidates": [
    {
      "primitive_id": "grp:customer_csv_to_crm_import@1",
      "match_path": "edge+schema+receipt_boost",
      "confidence": 0.87
    }
  ],
  "negative_memory_hits": [],
  "candidate": true,
  "serves_truth": false
}
```

## 13. Route Planning and Compilation

The route compiler transforms a task intent into an executable, auditable plan.

```text
UserIntent
-> PrimitiveDemand
-> CandidateBundle
-> RouteCandidateSet
-> PlanDelta
-> PlanLock
-> DeterministicExecution
-> ProofReceipt
-> PromotionEvidence or NegativeMemory
```

### PlanDelta

LLM or planner proposal. Not trusted yet.

```json
{
  "record_type": "plan_delta",
  "task_id": "task:customer_import_001",
  "selected_primitives": [],
  "selected_groups": [],
  "mutators": [],
  "assumptions": [],
  "proof_requests": [],
  "fallback_requests": [],
  "candidate": true,
  "serves_truth": false
}
```

### PlanLock

Deterministic compiled artifact. Trusted only after checks.

```json
{
  "record_type": "planlock",
  "planlock_id": "planlock:customer_import_001@sha",
  "input_edge": "CustomerCsv+CrmTarget+AuditPolicy",
  "output_edge": "CrmImportReceipt",
  "route_steps": [],
  "mutators": [],
  "runtime_targets": [],
  "effects": [],
  "policy_hash": "sha256:...",
  "route_hash": "sha256:...",
  "proof_plan": [],
  "compile_validation": {
    "edges_match": true,
    "schemas_match": true,
    "effects_allowed": true,
    "runtime_available": true
  },
  "candidate": true,
  "serves_truth": false
}
```

## 14. Proof and Promotion

Promotion requires receipts, not confidence.

Proof types:

```text
schema_validation
type_check
snippet_compile
import_smoke_test
unit_test
contract_test
fixture_behavior_test
golden_output_test
property_based_test
metamorphic_test
differential_test
sandbox_smoke_test
effect_audit
idempotency_test
state_diff_test
security_test
privacy_test
license_review
source_ref_review
benchmark_score_test
human_review_for_high_risk
```

Promotion lifecycle:

```text
L0 discovered candidate
L1 source-backed candidate
L2 contract extracted
L3 effects declared
L4 proof obligations generated
L5 route compiled
L6 PlanLock emitted
L7 deterministic execution tested
L8 receipt recorded
L9 benchmark score recorded
L10 promoted, deprecated, or negative-memory only
```

Never set `serves_truth=true` until promotion gates pass.

## 15. Ranking and Impact Scoring

Primitive score should use multiple signals:

```text
primitive_score =
  task_fit
+ source_authority
+ implementation_backing
+ proof_strength
+ route_reuse_count
+ benchmark_pass_rate
+ token_savings
+ runtime_success_rate
+ low_source_read_depth
+ cacheability
+ freshness
- false_positive_rate
- security_risk
- license_risk
- stale_contract_risk
- hidden_effect_risk
```

Route score:

```text
route_score =
  compile_success_probability
+ proof_pass_probability
+ expected_token_savings
+ expected_runtime_savings
+ expected_reuse_value
+ deterministic_fraction
- effect_risk
- source_fallback_cost
- human_review_cost
```

Generator score:

```text
generator_score =
  promoted_candidates / generated_candidates
  * average_reuse
  * benchmark_lift
  * source_authority
  / review_cost
```

Impact score:

```text
impact_score =
  frequency_of_problem
+ cost_of_naive_agent_solution
+ user_value
+ cross_industry_reuse
+ automation_potential
+ proofability
- safety_risk
- volatility
- implementation_cost
```

Capability score:

```text
capability_score =
  bare_model_failure_rate
+ primitive_lift_over_bare_model
+ route_success_rate
+ repeatability
+ coverage_of_common_inputs
+ coverage_of_common_outputs
+ proof_strength
```

## 16. Benchmark Strategy

Benchmarks are primitive factories, not just scoreboards.

Benchmark families to support:

```text
BFCL: tool/function selection primitives
DocILE: document extraction and line item primitives
SWE-bench Verified: repo repair and source escalation primitives
Terminal-Bench: CLI/runtime primitive wrappers
AppWorld: stateful API and tool route primitives
BigCodeBench: library/function composition primitives
LiveCodeBench: coding and repair primitives
MLE-bench/Kaggle: data science route templates
WebArena/Mind2Web: browser action and extraction primitives
OpenAPI/AsyncAPI suites: endpoint and event primitive factories
MCP Registry: agent tool primitive factories
Terraform/GitHub Actions/Kubernetes: cloud and deployment primitives
```

Benchmark arms:

```text
A0 reference/human solution
A1 baseline AI coding agent
A2 AI coding agent with repo/source search
A3 primitive-first exact route
A4 primitive-first deterministic template fill
A5 CandidateBundle + compact PlanDelta
A6 deterministic remix repair
A7 LLM micro-repair
A8 source-level fallback
A9 compiled-code fallback
```

Metrics:

```text
task_success
proof_success
tokens_to_plan
tokens_to_pass
runtime_llm_tokens
source_files_read
source_context_tokens
context_depth_to_solution
compile_success
route_reuse
new_group_created
negative_memory_created
cache_hit_rate
cost_per_success
latency_p50
latency_p95
unsafe_effect_count
human_review_needed
```

## 17. Telemetry and Experiment System

Every run should emit telemetry.

Core events:

```text
TaskReceived
TaskDecomposed
PrimitiveSearchStarted
CandidateBundleBuilt
PrimitiveRanked
ContextLevelOpened
RouteProposed
RouteCompiled
PlanLockCreated
ProofStarted
ProofPassed
ProofFailed
ModelInvoked
RankerInvoked
SourceSliceRead
CacheHit
CacheMiss
ArtifactWritten
ToolCalled
SideEffectObserved
NegativeMemoryWritten
PrimitivePromoted
PrimitiveDeprecated
SproutCreated
```

Run trace:

```json
{
  "run_id": "run:2026-07-02:000123",
  "task_id": "task:customer_import_001",
  "strategy_id": "strategy:primitive_route.v43",
  "experiment_arm": "champion",
  "model_components": [],
  "candidate_primitives": [],
  "selected_route": "route:customer_import.queue_safe@8",
  "context_depth": "L3_behavior_card",
  "source_files_read": 0,
  "source_tokens_read": 0,
  "planner_tokens": 1480,
  "runtime_llm_tokens": 0,
  "proofs": [],
  "cache": {
    "candidate_bundle_hit": false,
    "route_hit": true,
    "planlock_hit": false,
    "proof_receipt_hit": false
  },
  "scorecard": {}
}
```

## 18. Strategy Genomes

Every strategy must be versioned and replayable.

```json
{
  "strategy_id": "strategy:crm_import.v43",
  "task_family": "crm_import",
  "components": {
    "decomposer": "model_or_deterministic_component",
    "retriever": "hybrid_edge_schema_vector",
    "reranker": "ranker:primitive-crossencoder@5",
    "planner": "model_or_template_or_graph_planner",
    "compiler": "compiler:PlanDelta_to_PlanLock@4",
    "proof_policy": "contract+fixture+smoke",
    "cache_policy": "source_hash+contract_hash+route_hash"
  },
  "parameters": {
    "top_k": 80,
    "candidate_bundle_size": 12,
    "max_context_depth": "L5",
    "temperature": 0.1,
    "source_fallback_threshold": 0.62
  },
  "candidate": true
}
```

Run modes:

```text
champion: current best production path
challenger: competes against champion
shadow: runs but does not affect output
race: multiple paths run and first proof-passing route wins
quorum: multiple paths must agree for high-risk workflows
canary: small traffic slice
replay: historical task rerun
sprout: mutated variant with budget
benchmark_batch: standard benchmark suite
```

## 19. Models, LoRAs, Rankers, and Mini Agents

Models are components too.

Support:

```text
frontier LLM
OpenAI-compatible endpoint
Open WebUI endpoint
Ollama Cloud endpoint
local model where appropriate
embedding model
reranker
cross-encoder
LoRA adapter
small decomposition model
route-quality predictor
proof-failure predictor
source-escalation predictor
judge/evaluator model
guardrail model
```

Model component shape:

```json
{
  "model_component_id": "model:route_decomposer@1",
  "kind": "small_model|frontier_llm|embedding|reranker|judge|classifier|lora",
  "runtime": "local|cloud|vllm|api|batch",
  "input_edge": "TaskIntent+CandidatePrimitiveSummarySet",
  "output_edge": "DecomposedPrimitiveDemandSet",
  "cost_profile": {},
  "latency_profile": {},
  "quality_metrics": {},
  "supported_task_families": [],
  "version": "1.0.0",
  "candidate": true,
  "serves_truth": false
}
```

Provider rules:

```text
Use environment variables for keys.
Never commit keys, cookies, bearer tokens, browser storage, or passwords.
Prefer direct API mode when a stable bearer token exists.
Use browser-context mode only when explicitly needed and available.
One model call should produce one primitive, one PlanDelta, or one repair.
Do not batch hundreds of primitive rows in one model response.
```

Relevant env vars:

```bash
OPENWEBUI_BASE_URL=...
OPENWEBUI_MODEL=gemma-4-coding
OPENWEBUI_TOKEN=...
OPENWEBUI_CDP_URL=http://127.0.0.1:9222
OLLAMA_API_KEY=...
```

Do not place actual secret values in docs or source files.

## 20. Cache Layers

Cache more than final outputs.

```text
source_surface_cache: URL/package/spec hash -> parsed source surface
edge_card_cache: source hash + extractor version -> primitive candidates
candidate_bundle_cache: task embedding + filters -> ranked primitives
decomposition_cache: task pattern hash -> primitive demands
route_cache: input edge + output edge + policy -> route candidates
PlanLock_cache: route hash + runtime policy -> executable plan
proof_cache: PlanLock hash + fixture hash -> proof receipt
artifact_cache: input artifact hash + plan hash -> output artifact
negative_memory_cache: task pattern + primitive -> known failure
model_decision_cache: normalized prompt + model version -> reusable model output
```

Cache invalidation keys:

```text
source_hash
schema_hash
primitive_card_hash
route_hash
PlanLock_hash
policy_hash
model_version
lora_version
proof_version
runtime_version
```

## 21. Co-Occurrence and Group Creation

Learn which primitives often go together.

From every successful route, emit co-occurrence edges:

```json
{
  "cooccurrence_edge_id": "co:csv_parse.schema_validate@1",
  "from": "prim:csv.parse@1",
  "to": "prim:schema.validate@1",
  "relation": "often_precedes",
  "task_families": ["record_import", "crm_sync", "etl_load"],
  "support_count": 1842,
  "confidence": 0.91,
  "lift": 2.7,
  "median_tokens_saved_when_grouped": 0.78,
  "recommended_group_candidate": "grp:csv_to_validated_record_batch@1"
}
```

When support/confidence/lift are high:

```text
frequent route
-> route_to_group_card
-> hidden member edges
-> proof requirements
-> benchmark task set
-> candidate group
```

## 22. Negative Memory

Failures are useful artifacts.

```json
{
  "negative_memory_id": "neg:hubspot.deal.association_fetch@1",
  "applies_to": "grp:hubspot.deal_to_forecast_table@1",
  "failure_pattern": "Assumed deal object included full associated contact properties.",
  "reason": "Associations require separate fetches depending on endpoint and requested properties.",
  "recommended_fix": "Insert hubspot_association_fetch mutator before contact projection.",
  "suppresses": [
    "direct_deal_to_contact_projection_without_association_fetch"
  ],
  "candidate": true,
  "serves_truth": false
}
```

Negative memory should influence search and route ranking.

## 23. Common High-Value Primitive Families

Prioritize primitives that appear in many apps and workflows.

### Universal software/app primitives

```text
project scaffold
environment config
dependency bootstrap
healthcheck
structured logging
feature flags
user registration
login
password reset
email verification
MFA
OAuth/OIDC login
session refresh
logout/revocation
API keys
service accounts
RBAC
ABAC
tenant isolation
CSRF protection
rate limits
input validation
output sanitization
secret scanning
audit logs
security headers
encryption at rest
encryption in transit
CRUD resources
database migrations
seed data
soft delete/archive
search indexing
transactional outbox
cache layer
file upload
data import/export
customer tracker
lead tracker
support ticket tracker
subscription tracker
order tracker
inventory tracker
analytics tracker
notification center
forms
dashboards
admin CRUD pages
settings pages
checkout
onboarding
webhooks
queue workers
cron jobs
email/SMS services
CI/CD
container builds
Terraform deploys
Kubernetes deploys
logs/metrics/traces
alerts
incident runbooks
```

### Human/staff action primitives

```text
check_email
triage_inbox
reply_to_email
send_newsletter
schedule_meeting
reschedule_meeting
cancel_meeting
audit_record
double_check_decision
approve_request
reject_request
escalate_complaint
manage_complaint
issue_refund
renew_subscription
cancel_subscription
update_customer_record
merge_customer_records
search_customer_history
create_support_ticket
close_support_ticket
send_followup
generate_status_report
review_invoice
approve_invoice
reconcile_payment
```

### Data and entity primitives

```text
entity_resolution
entity_enrichment
entity_verification
source_authority_ranking
freshness_detection
fragile_context_detection
schema_mapping
data_merge
dedupe_cluster
identifier_normalization
address_normalization
phone_normalization
email_normalization
company_name_normalization
geography_specific_search
legal_source_search
jurisdiction_policy_check
BigQuery_entity_resolution
Splink_entity_resolution
tunable_entity_resolution
LSH_candidate_generation
blocking_key_generation
Manhattan_distance_match
cosine_similarity_match
Jaro_Winkler_match
leaf_record_processing
data_quality_receipt
```

### Visualization/game/rendering primitives

```text
math_visualization_generate
ThreeJS_scene_generate
ThreeJS_camera_fit
ThreeJS_interaction_controls
canvas_chart_render
SVG_diagram_generate
web_game_loop
game_entity_component_system
physics_step
collision_detection
raycast_pick
pathfinding_grid
sprite_atlas_load
texture_pack
shader_material
raytracing_scene_setup
rendering_performance_audit
memory_pool_allocator
object_pool
spatial_hash_grid
quadtree_index
octree_index
```

## 24. Source Adapter Priorities

Use source-backed adapters before synthetic generation.

High-value source surfaces:

```text
OpenAPI specs
AsyncAPI specs
GraphQL schemas
gRPC/protobuf definitions
MCP server manifests
PyPI packages
npm packages
GitHub Actions
Terraform Registry
Pulumi Registry
AWS Serverless Application Repository
Kubernetes CRDs
Helm charts
Artifact Hub
OperatorHub
Docker images
dbt packages
Airflow providers
n8n/Zapier/Make/Pipedream templates
Hugging Face models/datasets
Replicate models
Snowflake/Databricks/AWS data marketplaces
benchmark suites
official docs
repo source and tests
runtime traces
AI coding-session traces
```

Each adapter should emit:

```text
SourceSurfaceCard
PrimitiveCandidateSet
PrimitiveGroupCandidateSet
RuntimeWrapperCandidate
ProofObligationSet
LicenseReview
DeploymentRecipe
ReceiptSchema
NegativeMemoryHints
```

## 25. Orchestration Pattern

For each task:

```text
1. Normalize user intent.
2. Detect task family, domain, risk, runtime target, data sensitivity.
3. Search existing primitive cards.
4. Build CandidateBundle.
5. Search negative memory.
6. Produce route candidates.
7. Run deterministic mutator-assisted compilation where possible.
8. If needed, ask model for one PlanDelta or one primitive.
9. Compile PlanDelta into PlanLock.
10. Run proof obligations.
11. Emit receipts.
12. Update scorecards.
13. Cache decomposition, CandidateBundle, route, PlanLock, proof.
14. Promote, suppress, or write negative memory.
15. If route repeats, create a PrimitiveGroup candidate.
```

## 26. Immediate Work Claude Code Web Should Do

Start with concrete repo improvements, not more prose.

### A. Improve implemented-code primitive mining

Files:

```text
scripts/mine_implemented_code_primitives.py
data/dev-intel/implemented_code_primitives/
```

Tasks:

```text
1. Add import-smoke validation mode.
2. Add effect detection from AST: file, network, db, subprocess, shell, model call, env read, secret read.
3. Add dependency extraction from imports.
4. Add public API scoring.
5. Add fixture-generation placeholders per function signature.
6. Add per-record problem_solution fields.
7. Add JSON Schema for implemented_code_primitive_candidate.
8. Add validation script for generated JSONL.
9. Add a daily runner script that produces 1K records with checkpoints.
10. Add combined manifest builder with unique ID/dedupe verification.
```

### B. Build primitive import smoke runner

Create:

```text
scripts/smoke_implemented_code_primitives.py
```

It should:

```text
read implemented_code_primitives.jsonl
group by source module
try safe import when policy allows
record import pass/fail
detect import side effects conservatively
write import_smoke_receipts.jsonl
never execute arbitrary functions by default
```

### C. Build effect detector

Create:

```text
scripts/detect_code_primitive_effects.py
```

Detect from AST:

```text
open/pathlib file IO
requests/httpx/urllib/aiohttp network
subprocess/os.system shell
sqlite/postgres/db client usage
env var access
secret/token variable names
model/API calls
filesystem writes
random/time/non-determinism
```

### D. Build route portfolio generator

Create:

```text
scripts/build_route_portfolios_from_primitives.py
```

Inputs:

```text
implemented_code_primitives.jsonl
seed primitive candidates
known co-occurrence edges
```

Outputs:

```text
route_candidates.jsonl
route_portfolios.jsonl
group_candidates.jsonl
```

### E. Build strategy experiment schema

Create:

```text
schemas/strategy_genome.schema.json
schemas/run_trace.schema.json
schemas/scorecard.schema.json
```

and examples under:

```text
data/dev-intel/primitive_factory/examples/
```

### F. Add model-provider worker without committing secrets

Use environment variables only:

```text
OPENWEBUI_*
OLLAMA_API_KEY
```

The worker should support:

```text
one call = one primitive
checkpoint after every call
JSON-only response option
timeout/retry receipt
provider/model/version recorded
token usage recorded
all model outputs candidate=true and serves_truth=false
```

Do not block the deterministic 1K/day lane on model provider availability.

## 27. Acceptance Criteria for Next Improvement Pass

A meaningful next PR/change should produce at least one of:

```text
1,000 new source-backed implemented primitive candidates
or 250 import-smoke receipts
or 250 effect-audited primitive records
or 100 route candidates with proof obligations
or 50 primitive group candidates from co-occurrence
or a validated schema + checker for one record family
or a model-provider worker that successfully creates one checked primitive per call
```

Verification commands should be included in the final response.

## 28. Final Operating Rules

```text
Search first.
Reuse first.
Remix deterministically when possible.
Use LLMs for missing edges, not for bulk unverifiable filler.
One model call should produce one primitive, one route, or one repair.
Every output gets a record, hash, source/provenance, proof requirements, and candidate flags.
Receipts decide promotion.
Negative memory suppresses repeated mistakes.
Telemetry should make better paths win over time.
```

The north-star question:

```text
For this task, what is the cheapest route that compiles, proves, and reuses the most existing capability?
```

