# Claude/Fable Primitive Database Handoff

Last updated: 2026-07-01

This brief is for Claude/Fable or another coding agent picking up the primitive database work. It explains the product surfaces, the current primitive registry loop, why the work matters, and how to continue without breaking the truth boundary.

## One Sentence

We are building a searchable primitive database so AI coding agents can move from intent to compact edge search to reusable primitive/group to deterministic assembly and proof, instead of spending tokens recreating known software capabilities.

## Product Family

This is a portfolio-level handoff, not only an AIDevObserver note. Claude/Fable should keep the whole AI Done Right product family in view when changing primitive registry artifacts.

AI Done Right, also written in some notes as AIDoneRight, is the parent portfolio. The repo ships several surfaces that share one design system and one registry philosophy. AIDevExplorer is not a branded surface; treat `aidevexplorer` as a legacy/internal namespace for AIDevObserver benchmark-lab artifacts.

| Surface | Product job | Relationship to the primitive database |
|---|---|---|
| AI Done Right / AIDoneRight | Parent brand, portfolio hub, and business wrapper for the product family. | Explains the market thesis: reusable, proof-gated AI capability memory across products instead of isolated AI-agent work. |
| Teleon | Purpose-driven, eval-gated, self-adaptive compute/runtime layer. | Executes or assembles typed primitive groups. First-party deterministic groups live under `src/teleon/primitives/` and are proved with unit tests before becoming source-backed registry cards. |
| Baltor | Managed, verified, provable context. Baltor governs truth and depends on Teleon. | Consumes only promoted or otherwise truth-governed context artifacts. Candidate primitive cards can support planning and proof, but they must not be presented as truth-serving Baltor objects. |
| AIDevObserver | Observes AI-assisted development sessions, detects waste/reinvention, recommends reusable primitives, and owns the internal benchmark lab for primitive-first coding experiments. | Uses compact registry/search cards to tell an agent or developer when a known primitive, group, wrapper, proof, or benchmark route should be reused; benchmark-lab artifacts measure whether those routes beat baseline AI coding. |
| OpenHubForAI | Open registry/store for components, harnesses, skills, benchmarks, tools, rule packs, and primitive cards. | Provides the portable catalog substrate and schemas. Primitive artifacts should be shaped as registry rows/cards that can later be exported, searched, promoted, or consumed by other surfaces. |

Architecture law: Baltor depends on Teleon, and Teleon depends on OpenHubForAI. Do not invert this dependency.

Surface responsibilities:

```text
AI Done Right / AIDoneRight
-> packages the portfolio story, PMF, buyer segmentation, and public product narrative.

OpenHubForAI
-> stores portable component and primitive contracts: tools, harnesses, skills, benchmarks, rule packs, adapters, datasets, and candidate primitive cards.

Teleon
-> turns contracts into executable/evaluable runtime routes, deterministic adapters, proof receipts, and source-backed primitive groups.

Baltor
-> governs verified context and truth-serving artifacts; it should benefit from primitive proof gates without weakening the truth boundary.

AIDevObserver
-> observes real AI development work and recommends compact primitive reuse cards to reduce reinvention, token waste, missing proof, and hidden side effects.
-> owns the internal benchmark lab that stress-tests the registry by running tasks both ways: baseline AI coding versus primitive-first route assembly.
```

## Core Product Thesis

Most AI coding sessions waste context and money because the agent rereads implementation details or recreates common workflows from scratch.

The product changes the default loop:

```text
user intent
-> compact edge search
-> primitive or primitive group
-> deterministic adapters/mutators
-> implementation/proof
-> registry memory
```

The model should see the smallest useful object:

```text
visible input edge
+ visible output edge
+ blackbox behavior
+ side effects
+ runtime targets
+ proof status
+ promotion status
```

It should not see every hidden member edge unless it needs drill-down for proof or assembly.

## Primitive Model

### Primitive

A primitive is a reusable contract:

```text
InputEdge -> OutputEdge
```

It can be implemented as a Python function, API endpoint, webhook handler, queue worker, CLI command, CI workflow, Terraform module, Kubernetes job, UI component, RAG pipeline, or agent tool.

### Primitive Group

A primitive group is a larger reusable capability that hides many member edges behind one compact visible edge.

Example:

```text
RawCsvArtifact+ImportPolicy -> ValidatedImportReceipt
```

Hidden member edges can include parse, schema validation, field aliasing, dedupe, idempotency, persistence, audit receipt, and rollback checks.

### Runtime Shape

Runtime shape is how the reusable contract is exposed:

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

The same core group edge should be reusable across runtime shapes. Only the wrapper/adapters should change.

## Primitive Consumers And Graph Runtime

The primitive database is a shared interface layer for multiple product surfaces and internal consumers. The same primitive row or group card should be usable by Teleon, AIDevObserver, AIDevObserver's benchmark lab, Baltor, OpenHubForAI, and external coding agents, but each consumer reads it for a different purpose.

| Consumer | What it reads | What it does with primitives |
|---|---|---|
| Teleon | Typed primitive/group contracts, runtime targets, deterministic mutators, proof requirements, and source-backed implementation refs. | Orders primitives into an executable graph runtime, inserts adapters, runs proofs, emits receipts, and turns compact contracts into real runtime behavior. |
| AIDevObserver | Compact search cards, visible edges, blackbox summaries, effects, pitfalls, proof status, and promotion status. | Detects when an AI coding session is rebuilding known work, then recommends a reusable primitive route without dumping full code into the agent context. |
| AIDevObserver benchmark lab | Benchmark task decompositions, expected primitive cards, expected group cards, runtime-shape reuse cards, and token/proof plans. Legacy files may still use the `aidevexplorer` namespace. | Compares baseline coding against primitive-first graph assembly, then identifies which primitive routes repeatedly save tokens, reduce mistakes, and deserve promotion review. |
| Baltor | Promoted or truth-governed artifacts, proof receipts, provenance, privacy boundaries, and context contracts. | Consumes primitive outputs only when they satisfy the truth boundary; candidate cards can guide assembly and proof, but they must not become truth-serving context by implication. |
| OpenHubForAI | Portable catalog records, schemas, tools, harnesses, datasets, benchmarks, rule packs, adapters, and primitive cards. | Stores the open ecosystem substrate so primitives remain searchable, exportable, versioned, and reusable across products and coding-agent surfaces. |
| Coding agents and development tools | The smallest useful edge cards: input, output, blackbox behavior, effects, mutators, runtime target, proof status, and hidden-member summary. Current tool consumers include Codex, Claude Code, Kimi, GLM, and Gemma 4. | Solve large tasks by selecting and ordering known edges instead of rereading every implementation detail or regenerating every helper. |

The intended runtime loop is graph-shaped:

```text
UserIntent
-> EdgeSearch
-> CandidatePrimitiveRoute
-> GraphOrdering
-> AdapterMutatorInsertion
-> RuntimeAssembly
-> ProofExecution
-> ReceiptAndTrace
-> PromotionEvidence
```

A coding agent should usually see this:

```text
RawCsvArtifact+ImportPolicy -> ValidatedImportReceipt
effects: database_write, audit_log_write
mutators: api_endpoint_wrapper, idempotency_wrapper, output_wrapper
proof: fixture_import_test, idempotency_test, audit_receipt_test
promotion: candidate_only
```

It should not start by reading the parser, validator, dedupe implementation, database writes, audit logger, and retry logic. Those are hidden member edges for drill-down, proof, or implementation repair.

This is why primitive cards must be organized, small, searchable, and remixable:

```text
organized
-> stable IDs, source families, runtime shapes, primitive kinds, manifests, and promotion gates.

small
-> short visible edges and blackbox descriptions that fit inside coding-agent context windows.

searchable
-> natural-language terms, blocking keys, domains, input/output edge text, runtime targets, and proof/pitfall terms.

remixable
-> edges compose into larger routes, wrappers can change without rewriting core logic, and hidden member edges can be reused across benchmarks.

proof-aware
-> every route declares tests, receipts, side effects, and promotion blockers before it claims readiness.
```

Large real-world tasks should become ordered primitive graphs, not giant prompts. A benchmark like "build a secure CSV import API with preview, dedupe, audit logging, retry safety, dashboard visibility, and deployment readiness" should resolve into a route like:

```text
BenchmarkTaskIntent+TeamContext -> TaskAcceptanceContract
TaskAcceptanceContract+PrimitiveRegistry -> PrimitiveRouteCandidateSet
RawCsvArtifact+ImportPolicy -> ValidatedImportReceipt
ValidatedImportReceipt -> HttpResponse
ValidatedImportReceipt -> AuditReceipt
ServiceImage+RuntimePolicy -> DeploymentReadinessReceipt
BaselineTrace+PrimitiveRouteTrace+ComponentAttribution -> TokenComparisonReceipt
```

Teleon can assemble and prove that route. AIDevObserver can recommend it during a coding session. The AIDevObserver benchmark lab can score it against baseline AI coding. Baltor can consume only the promoted, truth-governed outputs and proof receipts. OpenHubForAI can store the portable cards and schemas that make the route searchable across tools.

## Truth Boundary

Every generated or source-backed candidate must preserve:

```text
candidate=true
serves_truth=false
```

Proof can move a candidate to a stronger readiness level, but it still does not serve truth until explicit owner review and promotion gates pass.

Promotion status to expect before owner review:

```text
proof_status=pass
promotion_gate_status=blocked_pending_owner_review
promotion_allowed=false
```

Do not use estimates as proof. Estimate-only benchmark token plans are for route selection and experiment planning, not promotion.

## Current Registry Lanes

Use these paths as the current source of truth. Read manifests for exact row counts.

### Source-backed primitive groups

```text
src/teleon/primitives/groups.py
tests/unit/test_teleon_primitive_groups.py
scripts/build_teleon_source_backed_primitive_group_cards.py
data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl
data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards_manifest.json
data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_proof_bundles.jsonl
data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_promotion_gates.jsonl
```

These are deterministic, unit-tested Teleon primitive groups loaded into AIDevObserver search.

### Benchmark task corpus

```text
catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/tasks.jsonl
catalog/knowledge-packs/data/aidevexplorer-real-world-build-tasks/manifest.json
data/dev-intel/aidevexplorer_task_benchmarks/<date>/suites.jsonl
data/dev-intel/aidevexplorer_task_benchmarks/<date>/manifest.json
```

This corpus is for baseline-vs-primitive experiments. It is candidate evidence, not a claim that every task came from a public repo.

### Benchmark decomposition lane

```text
data/dev-intel/aidevexplorer_task_benchmarks/2026-07-01/task_decompositions.jsonl
data/dev-intel/aidevexplorer_task_benchmarks/2026-07-01/task_decompositions_manifest.json
data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards.jsonl
data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards_manifest.json
scripts/build_aidevexplorer_benchmark_task_decompositions.py
scripts/check_aidevexplorer_benchmark_task_decompositions.py
scripts/build_aidevexplorer_benchmark_decomposition_cards.py
scripts/check_aidevexplorer_benchmark_decomposition_cards.py
```

This lane breaks benchmark tasks into logical primitive components and makes compact search cards by benchmark lens and task family.

The compact search-card layer now aggregates decomposition rows by:

```text
benchmark.decomposition.lens
benchmark.decomposition.task_family
benchmark.decomposition.expected_primitive
benchmark.decomposition.expected_group
```

The expected-primitive and expected-group cards are what make queries like CSV import, RAG citation search, OpenAPI schema validation, queue worker idempotency, and benchmark token proof land on a reusable route plan instead of a raw 10,000-row corpus. They remain route-selection aids only:

```text
candidate=true
serves_truth=false
estimate_only=true for token plans
actual_run_required=true before promotion evidence
```

### Runtime-shape reuse lane

```text
catalog/knowledge-packs/data/aidevexplorer-runtime-shape-tasks/tasks.jsonl
catalog/knowledge-packs/data/aidevexplorer-runtime-shape-tasks/manifest.json
data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards.jsonl
data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards_manifest.json
scripts/generate_aidevexplorer_runtime_shape_task_corpus.py
scripts/check_aidevexplorer_runtime_shape_task_corpus.py
scripts/build_aidevexplorer_runtime_shape_primitive_cards.py
scripts/check_aidevexplorer_runtime_shape_primitive_cards.py
```

This lane tests whether one reusable core edge can be exposed as functions, APIs, workers, jobs, dashboards, and microservices without rebuilding hidden logic.

### Primitive-kind family lane

```text
catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/families.jsonl
catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/manifest.json
data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards.jsonl
data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards_manifest.json
scripts/generate_aidevexplorer_primitive_kind_family_catalog.py
scripts/check_aidevexplorer_primitive_kind_family_catalog.py
scripts/build_aidevexplorer_primitive_kind_cards.py
scripts/check_aidevexplorer_primitive_kind_cards.py
```

This lane defines the taxonomy of useful primitive kinds: API endpoints, service groups, webhooks, queue workers, cron jobs, connectors, database changes, DevOps/IaC, RAG, security, UI, tests, and operations.

## Important Source-backed Groups Recently Added

The source-backed group registry includes deterministic functions for:

```text
decompose_benchmark_task_to_primitive_components
compare_benchmark_route_token_usage
ingest_benchmark_trace_pairs
evaluate_benchmark_trace_pair
evaluate_benchmark_route_promotion_candidate
evaluate_primitive_consumer_readiness
evaluate_primitive_registry_expansion_coverage
plan_primitive_graph_runtime
plan_runtime_shape_adapter
plan_runtime_shape_adapter_matrix
compile_openapi_endpoint_primitive_cards
compile_asyncapi_event_primitive_cards
compile_service_surface_primitive_cards
compile_container_runtime_primitive_cards
compile_kubernetes_workload_primitive_cards
compile_terraform_module_primitive_cards
compile_ci_workflow_primitive_cards
```

The trace-ingestion bridge turns raw benchmark run artifacts into evaluator-ready trace pairs:

```text
BenchmarkRunArtifactSet+TraceIngestionPolicy -> BenchmarkTraceIngestionReceipt
```

It pairs baseline and primitive artifacts by task, requires actual token counts, trace refs, successful runs, component attribution, primitive IDs, proof refs, route reuse, and candidate/truth boundaries, then emits `BaselineTrace+PrimitiveRouteTrace` records for the evaluator.

The measured trace bridge is especially important:

```text
BaselineTrace+PrimitiveRouteTrace+TracePolicy -> BenchmarkTracePairEvaluationReceipt
```

It rejects estimate-only token traces and requires actual token counts, same-task pairings, primitive usage, component attribution, proof refs, successful runs, and the candidate boundary.

The benchmark route-promotion bridge aggregates many measured runs into one candidate-only signal:

```text
BenchmarkTraceEvaluationSet+RoutePromotionPolicy -> BenchmarkRoutePromotionCandidateReceipt
```

It checks run count, task coverage, runtime-shape coverage, actual token-savings distribution, route reuse, proof refs, candidate/truth boundaries, and tool-consumer coverage for Codex, Claude Code, Kimi, GLM, and Gemma 4. This is the step between "one benchmark trace looks good" and "this route deserves owner promotion review"; it never promotes by itself.

The consumer-readiness bridge checks whether primitive cards are actually usable by the product family and development tools before route assembly:

```text
PrimitiveEdgeCardSet+ConsumerSurfacePolicy -> PrimitiveConsumerReadinessReceipt
```

It checks compact visible edges, blackbox summaries, search terms, hidden member edge coverage, adapter mutators, proof requirements, runtime targets, effects, and the candidate/truth boundary. It also carries tool-consumer gates for Codex, Claude Code, Kimi, GLM, and Gemma 4, because those tools should consume the same short cards instead of full source dumps.

The registry expansion coverage bridge answers "do we cover the primitive families the loop is supposed to cover?":

```text
PrimitiveRegistrySnapshot+ExpansionCoveragePolicy -> PrimitiveRegistryExpansionCoverageReceipt
```

It checks required primitive kinds, runtime targets, source families, proof-bundle coverage, search-smoke coverage, and candidate/truth boundaries. Use it before celebrating row count growth; more rows are not enough unless the registry covers API endpoints, microservices, webhooks, queue workers, cron jobs, CLI commands, workflows, Kubernetes jobs, dashboards, RAG/agent tools, database migrations, DevOps/IaC, security/policy, and integration connectors with searchable proof-gated cards.

The graph-runtime bridge is the direct answer to "how do coding agents consume primitives without reading full code?":

```text
UserIntent+PrimitiveEdgeCardSet+GraphPolicy -> PrimitiveGraphRuntimePlanReceipt
```

It takes compact edge cards, validates candidate-only boundaries, orders the visible edges into a route, aggregates hidden member edges, inserts adapter mutators, carries proof requirements/effects/runtime targets forward, and emits blockers when a route cannot safely assemble. Teleon uses it to plan execution. AIDevObserver can surface it as a reuse recommendation. The AIDevObserver benchmark lab can score the planned graph against baseline traces. Baltor should only consume outputs from the resulting route after the normal truth and promotion gates pass.

## How AIDevObserver Uses The Database

AIDevObserver should:

1. Observe the current session or code task.
2. Detect reinvention, oversized context, missing proof, missing runtime wrapper, or repeated helper implementation.
3. Query the registry through `src/teleon/observer/registry_search.py`.
4. Return compact reuse cards, not full source.
5. Prefer source-backed/proofed groups when relevant.
6. Show proof and promotion status.
7. Keep local/private source refs scoped correctly.
8. Never imply `serves_truth=true` for candidate rows.

Search path wiring currently includes:

```text
primitive_edge_cards.jsonl
curated_primitive_groups.jsonl
runtime_shape_primitive_cards.jsonl
primitive_kind_family_cards.jsonl
benchmark_decomposition_cards.jsonl
source_backed_primitive_group_cards.jsonl
```

## How The AIDevObserver Benchmark Lab Uses The Database

The benchmark lab is an internal experiment harness, not a branded surface. Its job is to compare:

```text
Run A: generic AI coding agent without primitive search
Run B: primitive-first route assembly with primitive/group search first
```

Measure:

```text
wall_clock_minutes
prompt_tokens
completion_tokens
primitive_search_tokens
primitive_component_tokens
custom_code_tokens
proof_tokens
rework_tokens
files_touched
test_pass_rate
pitfalls_avoided
primitive_groups_used
```

The point is not just to win on one task. The point is to find repeatable routes that should become promoted primitive groups.

## Benchmarks As Product Tooling

Benchmarks are not just eval reports. They are the factory for primitive discovery.

The useful benchmark loop is:

```text
task
-> decomposition into logical primitive components
-> baseline run
-> primitive-first run
-> paired trace evaluation
-> pitfall/proof scoring
-> route promotion evidence pack
-> owner review
-> promoted primitive group
```

This makes token usage accountable at component level. It answers:

```text
Which primitive saved tokens?
Which wrapper changed?
Which hidden member edge was reused?
Which proof requirement blocked promotion?
Which pitfall was avoided?
```

## Product-market Fit

The sharp wedge is not "another AI code assistant." It is AI development observability plus reusable capability memory.

Teams already use multiple AI coding tools. Their pain:

```text
agents repeat work
agents paste huge context
agents miss existing helpers
agents rebuild fragile glue
agents skip proof
agents hide side effects
teams cannot measure whether AI coding improved or just produced churn
```

AIDevObserver gives immediate value by reviewing AI-assisted sessions and recommending reusable primitives.

AIDevObserver's benchmark lab gives the deeper value by proving primitive-first development is faster, cheaper, and more reliable than baseline AI coding.

OpenHubForAI gives the ecosystem value by making reusable capabilities portable across teams, tools, and runtime surfaces.

Baltor benefits because verified context and truth-serving artifacts need a disciplined primitive/proof registry underneath.

Teleon benefits because runtime assembly needs typed, proof-gated building blocks.

## Buyer Segments

### First users

```text
solo developers using AI coding agents
freelancers shipping repeated SaaS/backend/data tasks
small product teams using Cursor/Claude/Codex/Copilot
AI-forward agencies doing many similar client builds
```

### Expansion users

```text
platform engineering teams
DevEx teams
security/compliance teams
data platform teams
enterprise AI enablement teams
```

### Why they buy

```text
lower token spend
less repeated implementation
better reuse
fewer side-effect mistakes
proof and audit trail for AI-generated work
visibility into whether AI coding is helping
portable registry memory across tools
```

## What Good Looks Like

A good primitive card:

```text
has one compact visible input edge
has one compact visible output edge
declares effects
declares runtime targets
has hidden member edges only for drill-down
has deterministic adapter mutators
has proof requirements
has source refs or implementation refs
is candidate-only until promotion
```

A good primitive group:

```text
collapses a repeated multi-step route
preserves enough hidden edges for audit
lets wrappers change without rebuilding core logic
has contract tests or unit tests
has promotion gates
is discoverable by natural language and edge query
```

A bad primitive:

```text
is just a vague idea
has no input/output contract
has no side-effect declaration
is only a copied code blob
is too tiny to reduce context
claims truth without proof
mixes estimates with measured evidence
```

## Current Commands

Run focused unit proof:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/unit/test_teleon_primitive_groups.py
```

Rebuild and check source-backed groups:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_teleon_source_backed_primitive_group_cards.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_teleon_source_backed_primitive_group_cards.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_teleon_source_backed_primitive_group_proof_bundles.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_teleon_source_backed_primitive_group_proof_bundles.py
```

Check benchmark decomposition lanes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_aidevexplorer_task_benchmark_suites.py --date 2026-07-01
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_aidevexplorer_benchmark_task_decompositions.py --date 2026-07-01
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_aidevexplorer_benchmark_decomposition_cards.py
```

Check runtime-shape and primitive-kind lanes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_aidevexplorer_runtime_shape_task_corpus.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_aidevexplorer_runtime_shape_primitive_cards.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_aidevexplorer_primitive_kind_cards.py
```

Check primitive lifecycle candidate boundary:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/primitive_source_lifecycle.py --self-test
```

Build docs:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m mkdocs build
```

## Search Smokes To Run

Use `registry_search_response` from `src.teleon.observer.registry_search`.

Useful queries:

```text
actual paired benchmark trace token proof component attribution primitive route
api benchmark decomposition token usage primitive components
csv import benchmark task family token comparison visible edges
rag retrieval benchmark decomposition proof token plan
security triage benchmark primitive components token attribution
container runtime primitive cards service image healthcheck secret refs
kubernetes workload primitive cards manifest image probe resource limits
terraform module primitive cards resource variables outputs tag policy
ci workflow primitive cards triggers jobs permissions artifacts
```

Expected behavior:

```text
source-backed or benchmark decomposition cards should appear near the top
candidate=true
serves_truth=false
proof_status=pass only for source-backed proofed groups
promotion_allowed=false unless explicit owner review exists
```

## What To Do Next

Immediate next loops:

1. Feed raw benchmark run artifacts through `ingest_benchmark_trace_pairs`.
2. Generate paired baseline/primitive trace receipts for a small sampled suite.
3. Feed those traces into `evaluate_benchmark_trace_pair`.
4. Aggregate repeated wins with `evaluate_benchmark_route_promotion_candidate` across runtime shapes and tool consumers.
5. Build route promotion evidence packs from measured trace receipts and candidate-route receipts.
6. Use `evaluate_primitive_consumer_readiness` to gate whether candidate edge cards are organized, compact, searchable, remixable, and usable by Codex, Claude Code, Kimi, GLM, Gemma 4, and the product surfaces.
7. Use `evaluate_primitive_registry_expansion_coverage` to audit required family/runtime/source/proof/search coverage before treating row count growth as progress.
8. Use `plan_primitive_graph_runtime` as the route-assembly bridge from edge-card search results to ordered graph runtime plans.
9. Add more source-backed primitive groups for integration connectors, workflow automations, API resource groups, and DevOps wrappers.
10. Keep search cards compact and aggregate high-volume corpora instead of loading every raw row into AIDevObserver search.
11. Keep documentation updated with exact file paths and commands.

Do not mark the primitive expansion goal complete. This is a multi-day loop; each pass should leave better registry cards, better proof gates, and better AIDevObserver search behavior.

---

## Appendix — Primitive Database Agent Brief

*Folded in 2026-07-03 from `primitive-database-agent-brief.md` (now archived). This is the tactical build brief — concepts, source surfaces, search lenses, edge mutators, quality bar, and copy-paste agent tasks — complementing the strategic handoff above. Copy it into another coding agent to continue expanding the primitive database.*

**Purpose:** give another AI agent enough context to search for, design, create, and improve useful reusable primitives and primitive groups for the AIDevObserver / Teleon / OpenHubForAI ecosystem.

Copy this document into another coding agent when you want it to continue expanding the primitive database.

### Mission

We are building a massive searchable primitive database so AI coding agents do not waste tokens recreating capabilities that already exist.

The goal is not just many tiny functions. The goal is:

```text
User intent -> compact edge search -> reusable primitive or primitive group -> deterministic assembly -> proof -> searchable registry memory.
```

The LLM should only see the smallest useful contract:

```text
visible input edge + visible output edge + blackbox behavior + effects + proof status
```

It should not read every internal function or edge unless it asks for drill-down.

### Core Concepts

#### Primitive

A primitive is a reusable capability with a clear blackbox contract.

Minimum useful fields:

```json
{
  "primitive_id": "prim:stable-id",
  "kind": "py.fn",
  "title": "Human readable title",
  "input_edge": "InputTypeOrEnvelope",
  "output_edge": "OutputTypeOrReceipt",
  "contract": {"input": "InputTypeOrEnvelope", "output": "OutputTypeOrReceipt"},
  "blackbox": {"does": "What it does without implementation detail."},
  "effects": [],
  "memory": "inline|artifact|external",
  "cache": "content_hash|policy_required|none",
  "runtime_targets": ["local.python", "container.python"],
  "proof_requirements": ["unit_test", "contract_test"],
  "candidate": true,
  "serves_truth": false
}
```

#### Primitive Group

A primitive group is a larger first-class capability made from smaller primitives, adapters, templates, and deterministic workers.

Primitive groups are essential because they reduce the number of edges the LLM has to understand.

Example:

```text
RawRecordBatch+ImportPreparationPolicy -> PreparedRecordImport
```

This one visible group edge can hide:

```text
field normalization
explicit aliases
collision preservation
required-field validation
identity dedupe
deterministic sort
schema fingerprint
idempotency key
```

The group card should expose one visible input/output edge and keep member edges in `group_contract.hidden_member_edges`.

Minimum group card shape:

```json
{
  "primitive_id": "grp:domain.capability@1",
  "kind": "artifact.primitive_group",
  "title": "Prepare record import group",
  "input_edge": "RawRecordBatch+ImportPreparationPolicy",
  "output_edge": "PreparedRecordImport",
  "contract": {
    "input": "RawRecordBatch+ImportPreparationPolicy",
    "output": "PreparedRecordImport"
  },
  "group_contract": {
    "visible_input_edge": "RawRecordBatch+ImportPreparationPolicy",
    "visible_output_edge": "PreparedRecordImport",
    "hidden_member_edges": [
      "RecordFields->NormalizedFields",
      "RecordBatch+IdentityFields->DedupedRecordBatch"
    ]
  },
  "blackbox": {
    "does": "Prepare imported records in one deterministic group.",
    "llm_context_policy": "show_group_edge_first; reveal member edges only on drilldown"
  },
  "candidate": true,
  "serves_truth": false
}
```

### Current Local Registry Lanes

Generated edge cards:

```text
data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl
```

Curated grouped primitive cards:

```text
data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl
```

Current grouped primitive code:

```text
src/teleon/primitives/groups.py
```

Current grouped primitive tests:

```text
tests/unit/test_teleon_primitive_groups.py
```

AIDevObserver searches both generated edge cards and curated group cards.

### What To Build

Prioritize primitives and groups that developers, data teams, operators, and business users repeatedly ask AI agents to recreate.

Good primitive-group categories:

- record import preparation
- file mutation with archive/manifest receipt
- API request validation + policy decision + persisted response
- browser extraction + table normalization + artifact export
- source discovery + dedupe + ranking + digest
- job description ingestion + skill extraction + role taxonomy mapping
- public procurement opportunity ingestion + NAICS/PSC extraction + deadline ranking
- GitHub repo scan + capability extraction + license gate
- PyPI/package scan + API surface extraction + edge cards
- n8n/Zapier workflow import + primitive route conversion
- Kaggle notebook/project analysis + pipeline primitive extraction
- log/session ingestion + action extraction + replay summary
- codebase scan + helper detection + reuse recommendation
- Kubernetes manifest validation + deployment readiness plan
- cloud function wrapper + request schema + response schema + local test harness
- SQL/CSV/Parquet data load + schema fingerprint + quality checks
- embedding/vector index build + retrieval proof
- policy/rule-pack evaluation + appeal/audit receipt

### Source Surfaces To Mine

Use source-backed public surfaces. Prefer official docs, package APIs, examples with licenses, and stable machine-readable feeds.

High-value surfaces:

- GitHub topics, trending repos, awesome lists, and source trees
- PyPI packages, package metadata, READMEs, examples, and typed APIs
- npm packages and workflow libraries
- official docs for common SDKs and APIs
- n8n templates, Zapier integrations, Make templates, Pipedream components
- Kaggle competitions, datasets, notebooks, and discussion posts
- Hugging Face models, datasets, Spaces, and papers
- YC AI directory, Product Hunt AI, Show HN, startup directories
- AI startup/tool directories and API docs
- developer-resource megarepos, algorithm repos, programming dictionaries
- USAJobs, OPM, SAM.gov, USASpending, Grants.gov, agency procurement pages
- NAICS/PSC/SIC datasets and crosswalks
- industry standards, compliance checklists, engineering runbooks
- public data catalogs, public APIs, government open data portals
- forums, RSS feeds, newsletters, and recurring engineering blogs
- non-English sources for common business/software workflows

Do not blindly copy code. Extract contracts, ideas, source refs, and implementation opportunities. Respect licenses and never republish restricted source.

### Search Strategy

For every source area, ask:

```text
What data enters?
What data leaves?
What deterministic transformations happen?
What side effects happen?
What proof would show this works?
Can this be grouped so the LLM sees fewer edges?
Can adapters make near-matches exact?
Can a deterministic worker build it without model codegen?
```

Use many search lenses:

```text
"how to build X"
"X checklist"
"X API reference"
"X examples"
"X template"
"X workflow"
"X open source"
"X data pipeline"
"X validation"
"X import export"
"X integration"
"X automation"
"X n8n"
"X zapier"
"X python package"
"X github"
"X schema"
"X benchmark"
"X public dataset"
```

Also search by role, industry, and object:

```text
role + task + input + output
industry + workflow + validation
department + report + data source
NAICS name + software workflow
government job title + recurring task
startup category + API workflow
```

### Primitive Generation Rules

Create source-backed or implementation-backed candidates only.

Do:

- keep `candidate=true` and `serves_truth=false` until promotion;
- include input/output edges;
- include side effects;
- include proof requirements;
- include source refs;
- include deterministic mutator options;
- prefer grouped primitives when a common route has many internal steps;
- write tests for implemented primitives;
- add small examples only when they prove the edge;
- keep LLM context compact.

Do not:

- create synthetic primitives with no source, code, or proof path;
- claim a primitive serves truth before proof and promotion;
- expose huge implementation context as the default search result;
- create one primitive per trivial line when a group edge is more useful;
- hide network, file, shell, database, or model-call effects;
- republish source from restricted references.

### Useful Edge Mutators

Mutators make near-matches usable without asking a coding agent to write glue.

Prioritize deterministic mutators:

- `map_sequence`: `A -> B` becomes `list[A] -> list[B]`
- `input_envelope_wrapper`: `A+B -> C` becomes `Envelope[A+B] -> C`
- `output_wrapper`: `A -> B` becomes `A -> Wrapped[B]`
- `field_rename`: explicit field aliasing
- `field_project`: keep required fields only
- `schema_validator_inserter`: add deterministic schema validation
- `type_cast`: declared scalar/path/string/dataclass casts
- `path_to_bytes`
- `bytes_to_text`
- `json_to_dataclass`
- `dataclass_to_json`
- `pagination_expander`
- `retry_wrapper`
- `cache_wrapper`
- `idempotency_wrapper`
- `artifact_materialize`
- `artifact_reference`
- `api_endpoint_wrapper`
- `cloud_function_wrapper`
- `kubernetes_job_wrapper`
- `pretooluse_hook_wrapper`
- `route_to_group_card`

Each mutator needs preconditions and proof obligations.

### Group Factory Pattern

When many primitives chain together, collapse them into a primitive group.

Process:

```text
1. Search primitive cards by requested input/output edges.
2. Build an exact edge route with deterministic graph search.
3. Insert deterministic adapters where allowed.
4. Prove the route with unit/contract tests.
5. Emit a group card with one visible input/output edge.
6. Store hidden member edges for drill-down.
7. Search the group card first next time.
```

Output:

```text
RoutePlan -> PrimitiveGroupCard
```

This is the main path to unlimited reusable groups without exploding LLM context.

### Quality Bar

A useful primitive or group should pass at least one of these:

- it is implemented locally and unit-tested;
- it is source-backed with clear API/docs references and proof plan;
- it maps to a common developer/business workflow;
- it reduces a multi-step LLM coding task to one deterministic edge;
- it has adapters/mutators that make it reusable across variants;
- it has a safe runtime target such as local Python, container Python, cloud function, Kubernetes job, or CLI.

Promotion requires stronger proof:

```text
source ref exists
license/policy reviewed
input contract validated
output contract validated
side effects declared
unit or smoke test passes
privacy boundary reviewed
runtime/resource profile declared
candidate remains serves_truth=false until promotion gate
```

### Example Tasks For Another Agent

Use these prompts:

```text
Search the provided source surfaces for recurring data import, validation, dedupe, and export workflows. Create 10 source-backed primitive group candidates with visible input/output edges, hidden member edges, source refs, mutators, and proof obligations.
```

```text
Mine PyPI packages in the web scraping, document parsing, CSV/Parquet, API validation, scheduling, and Kubernetes categories. Extract candidate primitive groups that hide multiple common steps behind one edge. Do not copy package code.
```

```text
Search n8n templates and Zapier app categories for common automation patterns. Convert them into primitive group candidates with trigger edge, action edge, effects, adapter options, and proof plan.
```

```text
Review USAJobs/SAM.gov/USASpending source surfaces and design primitive groups for job/opportunity ingestion, classification, NAICS mapping, deadline ranking, entity extraction, and alert generation.
```

```text
Read local source files and identify repeated internal routes that can be collapsed into primitive groups. Add tests and curated group cards for the strongest candidates.
```

### Expected Output Files

If implementing code:

```text
src/teleon/primitives/<domain>.py
tests/unit/test_teleon_<domain>_primitives.py
```

If adding curated group cards:

```text
data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl
```

If adding source maps or discovery seeds:

```text
catalog/knowledge-packs/data/<source-map-name>/*.jsonl
docs/codex/<brief-name>.md
```

### Final Operating Rule

The best primitive database is not a pile of code snippets. It is a searchable graph of compact, typed, proofable capabilities.

Default to this:

```text
Make the LLM choose or design the route.
Make deterministic workers execute, adapt, test, persist, and summarize it.
Make grouped primitives hide complexity behind one reusable edge.
```
