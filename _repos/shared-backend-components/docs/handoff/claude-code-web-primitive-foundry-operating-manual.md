# Claude Code Web Operating Manual: Primitive Foundry, Remixers, Route Compiler, and AIDevObserver Consumption

Paste this document into Claude Code on the web when continuing the primitive system.

The job is not to invent random rows. The job is to grow a useful, source-backed, proof-aware primitive bank that AIDevObserver can search and consume, then use telemetry and benchmarks to decide which generation, search, remix, and compile paths are best.

## 0. First Principles

The system should not commit to one way of generating primitives, one way of searching primitives, one compiler, one model, or one proof method.

Build a strategy tournament:

```text
source adapters
+ deterministic miners
+ LLM generators
+ local models / LoRAs / rankers
+ search methods
+ remixers / mutators
+ compilers
+ proof systems
+ benchmark arms
+ telemetry receipts
= promoted primitive routes, reusable primitive groups, and negative memory
```

The core question for every task:

```text
What is the cheapest route that compiles, proves, and reuses the most existing capability?
```

Never treat plausible generated content as truth. New rows remain:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

Promotion requires source refs, contract checks, effect declaration, proof receipts, and benchmark or fixture evidence.

## 1. Repo Orientation

Start here:

```text
README.md
AGENTS.md
CLAUDE.md
taxonomy/SPEC.md
docs/codex/no-magic-values.md
```

This repo is a specification, catalog, static site, and primitive foundry workspace for the AI Done Right product family:

```text
OpenHubForAI: open registry and schema layer
Teleon: purpose-driven, eval-gated compute runtime
Baltor: managed verified context
AIDevObserver: reviews and improves AI coding-agent usage
```

Do not create a disconnected primitive system. Extend the existing catalog, registry, scripts, and AIDevObserver search path.

## 2. Active Primitive Consumption Path

AIDevObserver consumes candidate primitives through these paths:

```text
src/teleon/observer/registry_search.py
src/teleon/observer/settings.py
scripts/_config.py
```

Important active sources:

```text
.agent/primitive-registry/primitive_candidate_records.jsonl
.agent/primitive-registry/primitive_search_index.jsonl
dist/primitive-registry-operational-load/
data/dev-intel/aidevobserver_edge_foundry/*.jsonl
data/dev-intel/implemented_code_primitives/daily_20260702_2k/implemented_code_primitives.jsonl
```

The implemented-code primitive lane is private/internal by default because it can expose local source paths and implementation-origin metadata. It should be searchable in local/private scope, not public-demo scope.

Use these checks after registry or primitive changes:

```bash
python3 scripts/check_aidevobserver_implemented_primitives_consumption.py
python3 scripts/check_aidevobserver_operational_primitive_search.py --self-test
python3 scripts/check_aidevobserver_local_registry_connector.py --self-test
python3 scripts/check_aidevobserver_session_benchmark.py --self-test
python3 scripts/check_aidevobserver_compiled_ai_evaluation.py --self-test
```

Use this command to read current counts rather than hand-typing stale values:

```bash
python3 - <<'PY'
from src.teleon.observer.registry_search import (
    load_edge_foundry_primitive_count,
    load_implemented_code_primitive_count,
    load_operational_primitive_count,
)
print("edge_foundry_records", load_edge_foundry_primitive_count())
print("implemented_code_records", load_implemented_code_primitive_count())
print("operational_records", load_operational_primitive_count())
PY
```

## 3. Primitive Record Types

Do not store only functions. Store capability records, route records, proof records, source records, and strategy records.

Core record families:

```text
PrimitiveCandidate
ImplementedCodePrimitiveCandidate
CapabilityCard
ProblemSolutionCard
PrimitiveGroup
RouteCandidate
RoutePortfolio
PrimitiveOverlay
RuntimeWrapper
SourceAdapter
ProofAdapter
BenchmarkAdapter
Mutator
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
ModelComponent
LoRAAdapter
RankerComponent
```

## 4. Compact Primitive Card Format

The LLM should first see the smallest useful contract:

```text
input edge
+ output edge
+ blackbox behavior
+ effects
+ runtime targets
+ proof status
+ source/provenance summary
```

Canonical candidate shape:

```json
{
  "primitive_id": "prim:domain.capability.variant@1",
  "record_type": "primitive_candidate",
  "kind": "primitive",
  "family": "domain.capability",
  "title": "Human readable capability",
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
    "problem": "Recurring problem this primitive solves.",
    "naive_agent_failure": "How agents usually waste time or break things.",
    "solution": "Reusable capability or route.",
    "core_components": [],
    "common_inputs": [],
    "common_outputs": [],
    "known_pitfalls": [],
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

Required rule: problem-solution details are first-class, not optional prose. A primitive should say which repeated problem it solves, which naive failure it prevents, which core components form the solution, and how success is measured.

## 5. Implemented Code Primitive Format

Implemented-code primitives come from deterministic AST mining of real code.

Shape:

```json
{
  "record_type": "implemented_code_primitive_candidate",
  "primitive_id": "impl:python.module.qualname.line24-8149c954@source",
  "kind": "implemented_code_primitive",
  "code_kind": "function",
  "language": "python",
  "module": "module.path",
  "qualname": "function_name",
  "signature": "def function_name(a: str) -> dict",
  "parameters": ["a"],
  "return_annotation": "dict",
  "source_path": "src/example.py",
  "source_span": {
    "start_line": 24,
    "end_line": 67
  },
  "input_edge": "PythonFunction[module.path.function_name]+InvocationPolicy+SourceContext",
  "output_edge": "PythonFunctionReceipt+dict",
  "blackbox": "Short behavior summary.",
  "contract": {
    "problem": "Reuse source-backed Python function without asking a model to recreate it.",
    "summary": "Behavior summary.",
    "input": "PythonFunction[module.path.function_name]+InvocationPolicy+SourceContext",
    "output": "PythonFunctionReceipt+dict",
    "errors": "import_side_effect; missing_dependency; behavior_not_fixture_verified; unsafe_runtime_effect"
  },
  "edge_contract": {
    "input_edge_description": "Call-site payload plus execution policy and source context.",
    "output_edge_description": "Receipt and return value.",
    "preconditions": "Module source parses and snippet compiles.",
    "postconditions": "Source span, code hash, signature, and blockers are recorded.",
    "failure_modes": "signature_mismatch; import_error; runtime_exception; missing_fixture; side_effect_not_declared",
    "composition_notes": "Generated by deterministic AST source mining."
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
    "source_span_present": true,
    "signature_extracted": true,
    "implementation_backed": true
  },
  "code_sha256": "sha256:...",
  "dedupe_key": "...",
  "generation_path": "deterministic_ast_source_mining",
  "verification_level": "L4_source_ast_snippet_compiled",
  "candidate": true,
  "serves_truth": false
}
```

Generate more implemented-code candidates with:

```bash
python3 scripts/mine_implemented_code_primitives.py \
  --source-root src/teleon \
  --source-root scripts \
  --limit 1000 \
  --run-id implemented_code_primitives_daily_YYYYMMDD_1k
```

Then run:

```bash
python3 scripts/check_implemented_primitive_compatibility.py \
  --input data/dev-intel/implemented_code_primitives/<run>/implemented_code_primitives.jsonl
```

## 6. Primitive Groups

Primitive groups hide a repeated route behind one compact visible contract.

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

Group promotion should come from repeated successful routes, not an LLM naming plausible chains.

## 7. Specialization Overlays

Do not physically generate every Cartesian product.

Store:

```text
base primitive
+ algorithm/data-structure overlay
+ data/schema overlay
+ storage/runtime overlay
+ website/source/API overlay
+ industry/domain overlay
+ region/legal overlay
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

Overlay shape:

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

## 8. Runtime Wrapper Primitives

The same core edge should lower into many runtime shapes:

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

Wrapper shape:

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

## 9. Mutators and Remixers

Mutators make near-matches usable without asking an agent to write unbounded glue.

### Deterministic Mutators

Use when behavior is mechanical:

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
fanout_fanin
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

Deterministic remix path:

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

Use deterministic search plus bounded LLM planning:

```text
CandidateBundle
+ compact primitive cards
+ allowed mutators
+ proof policy
-> LLM PlanDelta
-> deterministic compiler validates
-> PlanLock
```

The LLM proposes. The compiler decides.

### LLM Remix

Use for missing edges, unclear decomposition, or glue that cannot be handled deterministically.

Rules:

```text
1 model call = 1 primitive, 1 route, or 1 repair.
Do not ask for giant batches when generating promoted codeblocks.
Model output remains candidate=true, serves_truth=false.
Run deterministic validation after every call.
Checkpoint every accepted record.
```

### Genetic Mutators and Sprouts

Use in experiment mode to try variants with budgets and reproducible seeds.

Mutation operators:

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

Sprout record:

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

## 10. Search Portfolio

Do not use one retrieval method.

Search paths:

```text
exact edge search
type-compatible search
schema similarity search
BM25 / lexical search
dense vector search
hybrid lexical+vector search
graph route search
known-chain search
benchmark-demand search
receipt-boosted search
negative-memory suppression
source-authority ranking
cost-aware search
context-depth-aware search
```

Search returns a CandidateBundle, not one answer:

```json
{
  "candidate_bundle_id": "cb:crm_import:2026-07-02",
  "query_edge": "CustomerCsv+CrmTarget+AuditPolicy -> CrmImportReceipt",
  "candidates": [
    {
      "primitive_id": "grp:customer_csv_to_crm_import@1",
      "match_path": "edge+schema+receipt_boost",
      "confidence": 0.87
    },
    {
      "primitive_id": "grp:generic_record_import@1",
      "match_path": "subtype_graph",
      "confidence": 0.73
    }
  ],
  "candidate": true,
  "serves_truth": false
}
```

## 11. Route Compiler

The compiler transforms task intent into executable, auditable plans.

```text
TaskIntent
-> PrimitiveDemand
-> CandidateBundle
-> RouteCandidate
-> PlanDelta
-> PlanLock
-> DeterministicExecution
-> ExecutionReceipt
-> ProofReceipt
```

PlanDelta is model-proposed and untrusted:

```json
{
  "plan_delta_id": "delta:customer_import@candidate",
  "selected_primitives": [],
  "needed_mutators": [],
  "assumptions": [],
  "proof_requests": [],
  "candidate": true,
  "serves_truth": false
}
```

PlanLock is deterministic compiler output:

```json
{
  "planlock_id": "lock:customer_import.queue_safe@1",
  "input_edge": "CustomerCsv+ImportPolicy+CrmTarget",
  "output_edge": "CrmImportReceipt",
  "route_steps": [],
  "mutators": [],
  "runtime_targets": [],
  "effect_policy": {},
  "proof_requirements": [],
  "route_hash": "sha256:...",
  "policy_hash": "sha256:...",
  "candidate": true,
  "serves_truth": false
}
```

Execution should run from PlanLock, not free-form model text.

## 12. Proof and Promotion

Proof types:

```text
schema_validation
type_check
unit_test
contract_test
fixture_test
golden_output_test
property_based_test
metamorphic_test
differential_test
sandbox_smoke_test
static_analysis
effect_audit
state_diff_test
idempotency_test
security_test
privacy_test
cloud_dry_run
observability_receipt
human_review
benchmark_score_test
```

Lifecycle levels:

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

Promotion rule:

```text
No source refs -> no promotion.
No input/output edge -> no promotion.
No effect declaration -> no promotion.
No proof receipt -> no promotion.
No privacy/license review where relevant -> no promotion.
```

## 13. Ranking and Impact Scoring

Rank primitives by evidence and usefulness, not by how plausible they sound.

Primitive score:

```text
primitive_score =
  source_authority
+ proof_strength
+ route_reuse_count
+ benchmark_pass_rate
+ token_savings
+ runtime_success_rate
+ low_source_read_depth
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

Search score:

```text
search_score =
  primitive_recall_at_k
+ route_recall_at_k
- false_positive_route_rate
- unnecessary_source_drilldown_rate
```

## 14. Benchmarks and Experiment Arms

Benchmark arms:

```text
A0 reference / human solution
A1 baseline AI coding agent, no primitive search
A2 AI coding agent with repo search only
A3 primitive-first exact route
A4 primitive-first with deterministic mutators
A5 primitive-first with LLM PlanDelta
A6 deterministic remix repair
A7 LLM micro-repair
A8 source-level fallback
```

Metrics:

```text
task_success
tokens_to_plan
tokens_to_pass
runtime_llm_tokens
source_files_read
source_context_tokens
depth_to_solution
compile_success
proof_success
route_reuse
new_group_created
negative_memory_created
cost_per_success
human_review_needed
```

Benchmark source families to support:

```text
BFCL: tool/function routing
DocILE: document extraction and source-span proof
SWE-bench Verified: repo repair and source fallback
Terminal-Bench: CLI/runtime wrappers
AppWorld: stateful API tool routes
MLE-bench/Kaggle: data science routes
WebArena/Mind2Web: browser/action/extraction primitives
OpenAPI/AsyncAPI: endpoint/event primitive factories
MCP Registry: tool primitive factories
Terraform/GitHub Actions/Kubernetes: deployment primitives
```

## 15. Telemetry Ledger

Every run should emit traceable events:

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
LoRAInvoked
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

RunTrace shape:

```json
{
  "run_id": "run:2026-07-02:000123",
  "task_id": "task:crm_import_001",
  "strategy_id": "strategy:primitive_route.v43",
  "experiment_arm": "challenger",
  "model_components": [],
  "candidate_primitives": [],
  "selected_route": "route:customer_import.queue_safe@8",
  "context_depth": "L3_behavior",
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

## 16. Strategy Genome

Every path must be versioned and replayable.

```json
{
  "strategy_id": "strategy:crm_import.v43",
  "task_family": "crm_import",
  "components": {
    "decomposer": "model:local-decomposer@2",
    "retriever": "search:hybrid_edge_schema_vector@4",
    "reranker": "ranker:primitive-crossencoder@5",
    "planner": "model:gemma-4-coding@openwebui",
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
  "candidate": true,
  "serves_truth": false
}
```

Run modes:

```text
champion: current best production path
challenger: competes against champion
shadow: runs but does not affect output
race: multiple paths run and first proof-passing route wins
quorum: multiple paths must agree
canary: small traffic slice
replay: historical task replay
sprout: mutated variants under budget
benchmark_batch: standard suite run
```

## 17. Models, LoRAs, Rankers, and Mini-Agents

Treat intelligence components as records too:

```text
frontier LLM
OpenWebUI Gemma coding model
Ollama Cloud Kimi/GLM model
small local model
LoRA adapter
embedding model
reranker
classifier
decomposer
planner
compiler assistant
repair model
judge/evaluator
guardrail model
source adapter selector
cache-hit predictor
route-quality predictor
```

ModelComponent shape:

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
  "version": "0.1.0",
  "candidate": true,
  "serves_truth": false
}
```

Do not hardcode credentials. Use environment variables or a credential broker.

Provider env names used by local scripts:

```text
OPENWEBUI_BASE_URL
OPENWEBUI_MODEL
OPENWEBUI_TOKEN
OPENWEBUI_CDP_URL
OLLAMA_API_KEY
```

For high-volume LLM primitive generation, prefer one-call-one-primitive or one-call-one-repair. Avoid huge JSONL batches from models when output truncation can corrupt records.

## 18. Cache and Co-Occurrence

Cache layers:

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

Hash invalidation keys:

```text
source_hash
schema_hash
primitive_card_hash
route_hash
PlanLock_hash
policy_hash
model_version
LoRA_version
proof_version
runtime_version
```

Co-occurrence record:

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

When co-occurrence is strong:

```text
frequent route
-> route_to_group_card
-> hidden member edges
-> proof requirements
-> benchmark task set
-> candidate group
```

## 19. Negative Memory

Every failure should create structured memory.

Examples:

```text
primitive matched but wrong
adapter unsafe
schema drift
source stale
hidden side effect
auth scope missing
false positive benchmark match
LLM generated invalid JSON
proof failure caught silent field drop
```

Negative memory shape:

```json
{
  "negative_memory_id": "neg:hubspot.deal.associated_contact_properties@1",
  "applies_to": "grp:hubspot.deal_to_forecast_table@1",
  "failure_pattern": "Agent expects deal object to include full associated contact properties in the same response.",
  "reason": "Associations often require separate association/object fetches.",
  "recommended_fix": "Insert hubspot_association_fetch mutator before contact projection.",
  "suppression_policy": "demote_matching_route_candidates",
  "candidate": true,
  "serves_truth": false
}
```

Negative memory must influence search and route ranking.

## 20. High-Priority Primitive Domains

Prioritize domains that recur across software systems, staff workflows, and business operations:

```text
auth and identity
login and session management
password reset
MFA
OAuth/OIDC
RBAC/ABAC
tenant isolation
CRUD endpoints
admin dashboards
settings pages
customer trackers
lead trackers
support ticket trackers
subscription trackers
order trackers
inventory trackers
email send/reply/newsletter
calendar scheduling
refund/cancellation/complaint workflows
audit/double-check/review workflows
search operations
data merge operations
entity resolution
entity enrichment
data verification
fragile-context freshness
geography-specific search
legal/regulatory search
RAG citation validation
file upload/import/export
webhooks
queue workers
cron jobs
notifications
payments/billing
analytics events
observability
CI/CD
deployment wrappers
Kubernetes/Terraform
browser extraction
math visualization
Three.js visualization
web games
game engine workflows
rendering/raytracing
algorithms/data structures
LSH/similarity search
entity resolution with Splink/SQL/BigQuery
geospatial primitives
document extraction
guardrail primitives
agent tool-call safety
```

Each domain should produce:

```text
base primitive families
source adapters
runtime wrappers
proof adapters
benchmark adapters
negative memory
route portfolios
specialization overlays
problem-solution records
```

## 21. Source Adapter Priorities

High-value primitive factories:

```text
OpenAPI -> endpoint primitive cards
AsyncAPI -> event primitive cards
GraphQL -> resolver/query/mutation cards
gRPC/protobuf -> method primitive cards
MCP Registry -> tool primitive cards
Terraform Registry -> infra primitive cards
GitHub Actions -> CI/CD action cards
Kubernetes CRDs / Helm / Artifact Hub -> deployment cards
PyPI/npm packages -> API surface cards
dbt/Airflow/Dagster/Prefect -> data/workflow cards
n8n/Zapier/Make/Pipedream -> workflow group cards
Hugging Face/Replicate/model hubs -> model-call cards
Snowflake/Databricks/AWS Data Exchange -> data product cards
Benchmarks -> primitive demand cards
Runtime traces -> observed route cards
AI coding sessions -> reuse findings and negative memory
```

## 22. One-Primitive-at-a-Time LLM Generation

For model-generated codeblocks or records:

```text
1 input seed row
1 model call
1 primitive/codeblock/route/repair
1 validation pass
1 checkpoint write
```

Prompt contract:

```text
You are generating exactly one reusable primitive candidate.
Return one JSON object only.
Do not include markdown.
Do not claim the primitive is verified.
candidate must be true.
serves_truth must be false.
Include input_edge, output_edge, blackbox, effects, runtime_targets, proof_requirements, problem_solution, promotion_blockers, and source_refs if available.
```

If generating code:

```text
Return exactly one fenced code block.
No network, no subprocess, no secrets unless explicitly required and guarded.
Include a small deterministic self-test or fixture plan.
The codeblock remains candidate until compiled and tested.
```

## 23. Operational Loop for Claude Code Web

Follow this loop:

```text
1. Inspect existing artifacts and checks.
2. Choose one source lane or one seed pack.
3. Generate or mine a small batch.
4. Validate JSON/schema/compile.
5. Convert to AIDevObserver-compatible cards if needed.
6. Run AIDevObserver consumption checks.
7. Build route candidates or codeblocks.
8. Run proof scripts.
9. Write progress manifest.
10. Update scorecards.
11. Add negative memory for failures.
12. Create group candidates from repeated routes.
13. Do not promote without proof receipts.
```

Good next implementation tasks:

```text
scripts/build_route_portfolios_from_primitives.py
scripts/verify_implemented_code_import_smoke.py
scripts/build_problem_solution_cards_from_routes.py
scripts/train_or_score_primitive_cooccurrence.py
scripts/run_single_primitive_llm_compile.py
scripts/run_strategy_sprout_replay.py
scripts/check_strategy_scorecards.py
schemas/implemented_code_primitive_candidate.schema.json
schemas/strategy_genome.schema.json
schemas/route_candidate.schema.json
schemas/planlock.schema.json
```

## 24. Safety and Privacy Rules

Do not commit or print:

```text
API keys
bearer tokens
cookies
browser localStorage dumps
passwords
private user data
real PII in samples
```

Use env vars or credential broker paths. If a key is already in shell env, use it without writing it to files.

Public-demo surfaces must not expose local filesystem primitive rows. Private/internal AIDevObserver search can use local and implemented-code rows.

## 25. Verification Checklist Before Reporting Success

Before saying the system works, run relevant checks:

```bash
python3 scripts/check_aidevobserver_implemented_primitives_consumption.py
python3 scripts/check_aidevobserver_operational_primitive_search.py --self-test
python3 scripts/check_aidevobserver_local_registry_connector.py --self-test
python3 scripts/check_aidevobserver_session_benchmark.py --self-test
python3 scripts/check_aidevobserver_compiled_ai_evaluation.py --self-test
```

For implemented code primitive generation:

```bash
python3 scripts/check_implemented_primitive_compatibility.py \
  --input data/dev-intel/implemented_code_primitives/<run>/implemented_code_primitives.jsonl
```

For syntax checks, use in-memory compile if pycache writes are a problem:

```bash
python3 - <<'PY'
from pathlib import Path
for path in [
    Path("scripts/_config.py"),
    Path("src/teleon/observer/settings.py"),
    Path("src/teleon/observer/registry_search.py"),
]:
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
    print(f"ok {path}")
PY
```

## 26. Final Operating Rule

The primitive bank should improve itself through evidence:

```text
more tasks
-> more receipts
-> better rankers
-> better route reuse
-> fewer tokens
-> more proof
-> more promoted primitives
-> better future tasks
```

Do not optimize for row count alone.

Optimize for:

```text
verified useful primitives per day
route reuse
token savings
source-read reduction
proof pass rate
runtime success
lower false positives
better candidate ranking
more high-impact primitive groups
```

The durable asset is not the LLM output. The durable asset is:

```text
primitive contract
+ route
+ proof
+ wrapper
+ receipt
+ benchmark score
+ negative memory
+ promotion evidence
```

