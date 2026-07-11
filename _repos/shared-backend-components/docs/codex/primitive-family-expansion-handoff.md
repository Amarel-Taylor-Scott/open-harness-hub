# Primitive Family Expansion Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes expanding the
primitive database.

Status: execution brief. Counts below are snapshots. Recompute them from the
owning manifests before reporting progress.

## Current Count Snapshot

Computed locally from current manifests and JSONL rows:

| Scope | Count | Source |
| --- | ---: | --- |
| Verified factory primitive candidates | 28,796 | `data/dev-intel/primitive_factory/verified_candidates/*/manifest.json` |
| Source rows inspected by verifier | 30,824 | same manifests |
| Duplicate candidates removed | 477 | same manifests |
| Rejected candidates | 1,551 | same manifests |
| Linkable primitive cards | 28,741 | `data/dev-intel/primitive_factory/linkable_cards/2026-07-01/linkable_primitive_cards.jsonl` |
| Linkable primitive groups | 5,541 | `data/dev-intel/primitive_factory/linkable_cards/2026-07-01/primitive_group_index.jsonl` |
| High-leverage linkable cards | 22,172 | `data/dev-intel/primitive_factory/linkable_cards/2026-07-01/high_leverage_cards.jsonl` |
| Source-backed edge-foundry cards | 73,083 | `data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl` |
| Source-backed primitive-group cards | 194 | `data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl` |
| Runtime-shape primitive cards | 200 | `data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards.jsonl` |
| Primitive-kind family cards | 41 | `data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards.jsonl` |
| Searchable operational primitive records | 4,990 | `src.teleon.observer.registry_search.load_operational_primitive_count()` |

Interpretation: the headline number for the 2M primitive factory is **28,796
verified candidate primitives**. Do not confuse that with the wider source-backed
edge-card pool or the smaller operational registry export.

## Definition Shift

Treat primitives as families of reusable capability, not only callable
functions.

```text
Primitive database
  -> capability cards
  -> primitive groups
  -> route portfolios
  -> runtime wrappers
  -> source adapters
  -> proof adapters
  -> benchmark adapters
  -> negative memory
  -> promotion evidence
```

The useful unit is a compact, proof-aware edge contract that can be searched,
adapted, assembled, executed deterministically, measured, and promoted only
after source/proof gates pass.

## Problem-Solution Details

Do not force every primitive or group card to carry the full problem narrative.
Keep the primitive card compact, then link it to a problem-solution detail
record when build, repair, proof, or route selection needs more context.

The generated detail layer is:

```text
catalog/knowledge-packs/data/primitive-problem-solution-details/
```

It adds one detail record for each high-priority opportunity, covering problem
framing, user triggers, stakes, non-goals, solution route, transformations,
implementation notes, acceptance criteria, proof plan, failure modes,
troubleshooting hooks, negative memory queries, and synthetic example I/O.

Read:

```text
docs/codex/primitive-problem-solution-details-handoff.md
```

## Operating Law

More rows are not enough. Grow:

- more families;
- more source adapters;
- more route portfolios;
- more proof adapters;
- more negative memory;
- more benchmark hooks;
- more runtime wrappers.

Every generated row stays `candidate=true` and `serves_truth=false` unless a
separate owner-approved promotion path proves otherwise.

## First Expansion Packs

Build these as explicit packs, each with manifests, validation, and search
smoke tests.

| Pack | Target | Contents |
| --- | ---: | --- |
| `meta_compiler_primitives` | 25,000 | edge inference, contract diff, mutator selection, route planning, PlanDelta parsing, PlanLock compilation, proof generation, receipt validation, promotion gating, negative memory |
| `runtime_wrappers` | 50,000 | API endpoints, queue consumers, webhooks, cron jobs, workflow steps, Airflow tasks, Temporal activities, Prefect flows, Dagster assets, Argo workflows, GitHub Actions, Kubernetes jobs, cloud functions, CLI commands, MCP tools |
| `source_adapters` | 100,000 | OpenAPI, AsyncAPI, GraphQL, gRPC/protobuf, PyPI, npm, GitHub, GitHub Actions, Terraform Registry, Docker Compose, Helm, Kubernetes, dbt, Backstage, OpenTelemetry, Kaggle, OpenML, Hugging Face, benchmark suites, docs sites |
| `business_capability_groups` | 100,000 | customer, invoice, payment, order, shipment, claim, contract, vendor, employee, candidate, ticket, lead, opportunity, product, inventory, asset, appointment, project, incident, metric |
| `benchmark_to_primitive_demand` | 50,000 | coding, tool-use, browser, OS/app, document extraction, ML/Kaggle, RAG/retrieval, security, visual/media benchmarks |

## Required Meta-Primitives

Seed these before adding large domain packs:

| Primitive | Input edge | Output edge |
| --- | --- | --- |
| `edge_signature_infer` | `SourceSlice+Examples` | `InputEdge+OutputEdge` |
| `blackbox_summary_emit` | `SourceRefs+Examples+Tests` | `BlackboxBehaviorCard` |
| `effect_detector` | `SourceSlice+RuntimeTrace` | `EffectSet` |
| `proof_obligation_emit` | `PrimitiveCandidate` | `ProofRequirementSet` |
| `source_ref_resolver` | `UrlOrPackageRef` | `ResolvedSourceRefBundle` |
| `license_gate` | `SourceRefBundle` | `LicenseReviewReceipt` |
| `candidate_pack_ranker` | `PrimitiveCandidateSet+Intent` | `RankedCandidateBundle` |
| `contract_diff` | `RequestedEdge+CandidateEdge` | `GapAnalysis+AdapterPlan` |
| `mutator_selector` | `ContractDiff+AllowedMutators` | `MutatorPlan` |
| `route_planner` | `InputEdge+OutputEdge+PrimitiveGraph` | `RoutePlan` |
| `route_to_group_card` | `RoutePlan+ProofReceipt` | `PrimitiveGroupCard` |
| `negative_memory_writer` | `FailedRoute+FailureReason` | `NegativeMemoryRecord` |
| `context_receipt_emit` | `Task+LevelsRead+Tokens` | `ContextReceipt` |
| `plan_delta_parser` | `LLMPlanTextOrJson` | `ValidatedPlanDelta` |
| `plan_lock_compiler` | `PlanDelta+RoutePlan+Policy` | `PlanLock` |
| `runtime_receipt_validator` | `PlanLock+ExecutionTrace` | `ExecutionReceipt` |
| `promotion_gate_eval` | `Candidate+Proofs+SourceRefs` | `Promote/Deny/NeedsEvidence` |

## Proof Primitive Families

Most registries catalog tools. This registry must also catalog proof routes.
Add these as first-class primitive families:

- `unit_test_generate`
- `contract_test_generate`
- `golden_fixture_emit`
- `smoke_test_runner`
- `schema_roundtrip_test`
- `idempotency_test`
- `side_effect_audit`
- `privacy_boundary_test`
- `pii_redaction_test`
- `rate_limit_test`
- `retry_safety_test`
- `rollback_test`
- `snapshot_regression_test`
- `data_quality_test`
- `benchmark_score_test`

Promotion requires proof, not model confidence.

## Runtime Wrapper Families

The same core edge should be exposable across runtime shapes:

```text
py.fn
ts.fn
api.endpoint
graphql.resolver
grpc.method
mcp.tool
cli.command
queue.consumer
cron.job
webhook.handler
workflow.step
airflow.task
temporal.activity
kubernetes.job
cloud_function
github.action
browser.script
```

Required wrapper primitives:

- `py_fn_wrapper`
- `ts_fn_wrapper`
- `fastapi_endpoint_wrapper`
- `graphql_mutation_wrapper`
- `grpc_method_wrapper`
- `mcp_tool_wrapper`
- `cli_command_wrapper`
- `queue_worker_wrapper`
- `cron_job_wrapper`
- `webhook_handler_wrapper`
- `kubernetes_job_wrapper`
- `cloud_function_wrapper`
- `github_action_wrapper`
- `browser_automation_wrapper`

## Source Adapter Families

Source adapters are the growth engine. Each adapter should emit:

```text
SourceRefBundle
CandidatePrimitiveSet
CandidateGroupSet
RuntimeShapeVariants
ProofObligationSet
LicenseReviewObligation
BenchmarkTaskCandidates
NegativeMemoryHints
```

Prioritize adapters for:

- OpenAPI, AsyncAPI, GraphQL, and protobuf/gRPC;
- PyPI, npm, GitHub repos, and GitHub Actions;
- Terraform modules, Helm charts, Docker Compose, and Kubernetes manifests;
- Airflow, Prefect, Dagster, Temporal, and Argo workflow definitions;
- dbt projects, semantic-layer assets, and metric catalogs;
- Backstage catalog files and service metadata;
- OpenTelemetry traces/logs/metrics and incident artifacts;
- Kaggle, OpenML, Hugging Face datasets, and benchmark suites;
- documentation sites, package examples, and engineering blogs.

Verify external source docs before treating an adapter as source-backed. Until
then, rows are intake candidates only.

## Route Portfolio Records

A primitive may have multiple safe routes by scale, cost, latency, effect, and
proof strength.

Required records:

```text
CapabilityDemand
PrimitiveSupply
RouteQuote
RoutePlan
RouteExecution
RouteReceipt
RouteReview
NegativeMemory
PromotionEvidence
```

Route portfolios should rank alternatives by:

- data size;
- external side effects;
- audit requirement;
- latency budget;
- proof strength;
- cost;
- available runtime target;
- source confidence.

## Context Ladder Families

Support nesting-doll context disclosure:

```text
lod_l0_index_card_emit
lod_l1_edge_card_emit
lod_l2_contract_card_emit
lod_l3_behavior_card_emit
lod_l4_route_card_emit
lod_l5_proof_card_emit
lod_l6_source_slice_pack
lod_l7_full_source_escalation
context_depth_policy_select
drilldown_reason_classify
context_receipt_emit
source_read_budget_enforce
```

AIDevObserver should prefer the shallowest sufficient level, then record a
receipt when deeper source is needed.

## Negative Memory Families

The registry should remember bad matches:

- `failed_route_classify`
- `near_match_failure_record`
- `primitive_misuse_detect`
- `known_bad_adapter_record`
- `contract_overclaim_detect`
- `source_staleness_record`
- `hallucinated_api_record`
- `unsafe_effect_record`
- `benchmark_failure_to_negative_memory`
- `negative_memory_retrieval`

Negative memory is candidate planning evidence, not truth.

## Business Capability Families

Use business object packs to drive realistic scale:

- customer, invoice, payment, order, shipment, claim, contract, vendor;
- employee, candidate, ticket, lead, opportunity, product, inventory, asset;
- appointment, project, incident, metric, document, policy, account.

Each industry pack should emit:

```text
BusinessObjectTaxonomy
CommonTaskSet
PrimitiveDemandSet
IntegrationSurfaceSet
ProofPolicySet
BenchmarkTaskSet
NegativeMemorySet
```

## Base Record Shape

Use this minimal schema shape for new group ideas:

```json
{
  "primitive_id": "grp:domain.capability.variant",
  "kind": "artifact.primitive_group",
  "family": "domain.capability",
  "title": "Human-readable capability",
  "input_edge": "InputEnvelope+Policy",
  "output_edge": "OutputArtifact+Receipt",
  "blackbox": {
    "does": "What it does without implementation detail.",
    "llm_context_policy": "show_edge_first; drilldown_on_contract_or_proof_need"
  },
  "group_contract": {
    "visible_input_edge": "InputEnvelope+Policy",
    "visible_output_edge": "OutputArtifact+Receipt",
    "hidden_member_edges": []
  },
  "effects": [],
  "runtime_targets": [],
  "source_surfaces": [],
  "mutators": [],
  "proof_requirements": [],
  "benchmark_hooks": [],
  "negative_memory": [],
  "candidate": true,
  "serves_truth": false
}
```

Note: do not put `@1`, `v1`, or version strings into new IDs. Version belongs
in metadata, not names.

## Customization Overlays

After seeding broad families, specialize them through overlays instead of
copy-pasting primitive rows. Read
`docs/codex/primitive-customization-overlays-handoff.md` and expand:

```text
base capability
  + canonical object
  + platform or website overlay
  + industry policy
  + schema map
  + runtime wrapper
  + proof overlay
  = specialized primitive
```

The seed pack is:

```text
catalog/knowledge-packs/data/primitive-customization-overlays/
```

Validate it with:

```bash
python3 scripts/check_primitive_customization_overlays.py --self-test
```

## Variation Dimension Atlas

Use the variation atlas to avoid materializing impossible Cartesian products.
Read `docs/codex/primitive-variation-dimension-atlas-handoff.md` and seed from:

```text
catalog/knowledge-packs/data/primitive-variation-dimension-atlas/
```

The rule is:

```text
basic computer logic primitive
  + algorithm/data-structure
  + schema/storage/runtime/source/industry/region/role/proof overlays
  = resolved specialized primitive
```

Validate it with:

```bash
python3 scripts/check_primitive_variation_dimension_atlas.py --self-test
```

## Cloud Guardrail Runtime

Guardrails should be vendor-neutral primitive packs, not a Bedrock-specific
surface. Read `docs/codex/primitive-cloud-guardrail-runtime-handoff.md` and
seed from:

```text
catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/
```

Cloud/provider products are adapters; the primitive contract, deployment
wrapper, policy backend, and receipt schema stay portable.

Validate it with:

```bash
python3 scripts/check_primitive_cloud_guardrail_runtime.py --self-test
```

## High-Priority Opportunity Rankings

Use `docs/codex/high-priority-primitive-opportunity-rankings-handoff.md` and:

```text
catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings/
```

This pack ranks 1,000 candidate opportunities across module specialties,
industries, route variants, input/output edges, transformations, source-surface
hints, proof requirements, and negative-memory queries.

Validate it with:

```bash
python3 scripts/check_high_priority_primitive_opportunity_rankings.py --self-test
```

## Marketplace Source Surfaces

Use `docs/codex/marketplace-primitive-source-surfaces-handoff.md` and:

```text
catalog/knowledge-packs/data/marketplace-primitive-source-surfaces/
```

This pack treats MCP registries, OpenAPI directories, Terraform/Pulumi/CDK,
GitHub Actions, serverless apps, workflow templates, Kubernetes packages,
model hubs, data marketplaces, package registries, and cloud marketplaces as
primitive factories.

Validate it with:

```bash
python3 scripts/check_marketplace_primitive_source_surface_pack.py --self-test
```

## Agent Graph Path Mixtures

Route portfolios should also support mixtures of agent roles, troubleshooting
playbooks, and country or industry overlays. Read
`docs/codex/primitive-agent-graph-path-mixtures-handoff.md` and seed from:

```text
catalog/knowledge-packs/data/primitive-agent-graph-path-mixtures/
```

The resolver should combine candidate primitives with an agent path family,
fallback route variants, negative-memory queries, and jurisdiction-specific
proof obligations before compiling a PlanLock.

Validate it with:

```bash
python3 scripts/check_primitive_agent_graph_path_mixtures.py --self-test
```

## Highest-Leverage Group

The most important recursive primitive group is:

```text
SourceSurfaceRef+ExtractionPolicy+LicensePolicy
  -> PrimitiveCandidateSet+ProofObligationSet+SourceRefBundle
```

It should mine a source surface for public, source-backed primitive candidates
without copying restricted implementation code.

Hidden member edges:

```text
SourceSurfaceRef -> ResolvedSourceRefBundle
ResolvedSourceRefBundle -> CandidateCapabilityMentions
CandidateCapabilityMentions -> InputOutputEdgeCandidates
InputOutputEdgeCandidates -> PrimitiveCandidateSet
PrimitiveCandidateSet -> ProofObligationSet
```

Required proof requirements:

- source ref resolution;
- license policy review;
- candidate schema validation;
- no restricted source copy check;
- candidate/truth boundary check.

## First Commands

Recompute counts:

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path("data/dev-intel/primitive_factory/verified_candidates")
print(sum(int(json.loads(p.read_text()).get("verified_count") or 0) for p in root.glob("*/manifest.json")))
PY

python3 - <<'PY'
from src.teleon.observer.registry_search import load_operational_primitive_count
print(load_operational_primitive_count())
PY
```

Run coverage and search gates:

```bash
python3 scripts/check_aidevobserver_operational_primitive_search.py --self-test
python3 scripts/check_aidevobserver_primitive_kind_family_catalog.py --self-test
python3 scripts/check_primitive_customization_overlays.py --self-test
python3 scripts/check_primitive_variation_dimension_atlas.py --self-test
python3 scripts/check_primitive_agent_graph_path_mixtures.py --self-test
python3 scripts/check_primitive_cloud_guardrail_runtime.py --self-test
python3 scripts/check_high_priority_primitive_opportunity_rankings.py --self-test
python3 scripts/check_marketplace_primitive_source_surface_pack.py --self-test
python3 scripts/check_aidevobserver_example_sessions.py --self-test
python3 scripts/check_surface_server.py --self-test
```

Before celebrating any new pack, add a focused checker that proves:

- row count changed;
- IDs are stable and version-free;
- every row is candidate-only;
- every row has visible input/output edges;
- proof requirements are present;
- runtime targets are declared;
- at least one search smoke returns rows from the new family;
- source-backed claims have source refs and license-review obligations.
