# Teleon Architecture Routes And Fallbacks

This document memorializes the multi-route architecture for Teleon primitive planning, Python authoring,
LLM boundaries, deterministic compilation, runtime execution, and proof-gated promotion.

The goal is not to pick one permanent syntax or one universal planning format. The goal is to support
multiple compatible routes, choose the cheapest deterministic route first, use the least-token LLM route
that is likely to compile, and fall back to richer or more expensive routes only when needed.

## Core Law

```text
Objects are for construction.
Canonical records are for registry truth.
Compact generated views are for search and LLM planning.
PlanDelta is candidate intent.
PlanLock is execution truth.
Ledger events are observed reality.
Proof and promotion decide served truth.
```

Every supported route must compile into the same underlying truth boundary:

```text
CandidateBundle / Python authoring object
  -> resolved primitive records
  -> compiler checks
  -> optional registered remixes
  -> PlanLock
  -> runtime execution
  -> ledger/proof/promotion
```

## Why Multiple Routes

Different contexts optimize for different costs.

```text
Lowest LLM tokens:
  local aliases, dense PlanDelta, no source

Best Python readability:
  object-first primitives, function composition, template class fill

Best explicit control:
  primitive handles and verbose step specs

Best auditability:
  canonical records, verbose PlanLock, proof reports

Best repairability:
  richer ViewProfile, explicit PlanDelta pairs, deterministic RemixSurface

Best production safety:
  promoted composites, R8/R9 primitives, strict PlanLock execution
```

The router should not globally prefer one representation. It should select the cheapest route that meets
the current readiness, determinism, policy, and compile-success requirements.

## Stable Architectural Split

The system should maintain these separate objects:

```text
PrimitiveIdentity      stable registry identity
CallableSurface        observed Python evidence
PrimitiveRecord        canonical registry row
ViewProfile            generated compact/debug/canonical view
CandidateBundle        LLM/search boundary object
PlanDelta              compact candidate choice/patch from LLM or deterministic selector
RemixSurface           deterministic mutation menu
VariationRecord        durable record of every applied remix
PlanLock               deterministic execution manifest
LedgerEvent            observed runtime fact
PromotionRecord        permission to serve truth
```

Python introspection is evidence, not identity. Canonical identity should be stable across compatible file
moves, wrapper changes, aliases, and refactors.

## Route Families

### A. Python Authoring Routes

All Python authoring routes must compile into the same primitive handles and step specs.

| Route | Shape | Best For | Risk |
| --- | --- | --- | --- |
| Function-preserving metadata | `@primitive_metadata` + `P(fn)` | compatibility with normal Python functions, decorators, IDEs, pytest | slightly more verbose |
| Object-returning primitive | `@primitive` returns `Primitive` | very clean local composition | can surprise tools expecting a function |
| Explicit constructor | `Pipeline.chain(a, b, c)` | readability, codegen, unfamiliar contributors | more ceremony |
| Operator composition | `a >> b >> c` | literate pipelines | can become opaque if overused |
| Primitive handles | `primitive_handle(fn, ...)` | explicit metadata override | more verbose |
| Object graph | lists/dicts/matrices of primitives | grouped composition and phase structure | needs strict no-arbitrary-crawl rule |
| Opt-in object graph | `to_teleon_primitives()` | domain bundles | requires clear opt-in protocol |
| Template class fill | `InvoiceReview(normalize=..., emit=...)` | typed slots and reusable templates | not yet implemented |

Policy:

```text
No route is privileged as truth.
All routes compile to the same IR/step specs.
The benchmark selects best-by-lane.
```

### B. LLM Context Routes

The LLM should receive the cheapest ViewProfile likely to preserve compile success.

| Profile | Example | Use |
| --- | --- | --- |
| alias_only | `C3.0` | repair when context is already cached |
| signature | `C3.0 RawRateText>NormalizedRate` | simple slot fill |
| planning | `C3.0 norm_rate RawRateText>NormalizedRate fx:0 tools:map tr:V` | default compact planning |
| evidence | `C3.0 norm_rate RawRateText>NormalizedRate fx:0 tools:map proof:P succ:.94 cost:L tr:V` | ambiguous ranking |
| debug | verbose card subset | repeated compile failure |
| canonical | full record | offline audit, not normal LLM input |
| source | source snippet | last resort |

Policy:

```text
Never start with source if a generated view can answer the planning question.
Escalate view richness only after compile failure, ambiguity, or policy need.
```

### C. PlanDelta Routes

PlanDelta is candidate intent. It is not executable truth.

| Profile | Shape | Best For |
| --- | --- | --- |
| dense | `{"v":1,"p":"dense","t":0,"b":[0,0,0],"r":[[2,"map"]],"g":[]}` | fixed slot order, minimum tokens |
| pairs | `{"v":1,"p":"pairs","t":0,"b":[[0,0],[1,0]],"r":[[2,0,"map"]],"g":[]}` | optional slots, branches, debug |
| patch | `{"v":1,"p":"patch","replace":[[2,1]],"remix":[[3,"map"]],"g":[]}` | repair loops |
| gap | `{"v":1,"p":"gap","g":[{"s":2,"need":"A>B","why":"no verified candidate"}]}` | missing primitive/remix |
| explain-only | no executable delta | human review and debugging |

Policy:

```text
Dense PlanDelta is an optimization, not the baseline contract.
Pairs PlanDelta is the safer general form.
Patch PlanDelta is preferred after a compiler diagnostic.
```

### D. Compiler Repair Routes

The compiler should try deterministic repair before asking for more LLM output.

| Problem | First Route | Fallback |
| --- | --- | --- |
| scalar primitive selected for list slot | `map_sequence` remix | ask for alternative candidate |
| field mismatch | `field_rename` or `field_projection` remix | ask for binding patch |
| output needs envelope | `output_wrapper` remix | ask for alternative candidate |
| large inline output | force `ArtifactRef` adapter | reject if primitive cannot support artifact mode |
| missing required gate | insert registered gate if policy allows | reject or ask for template repair |
| side effect before gate | reorder if dependencies allow | reject |
| runtime mismatch | worker/container adapter | ask for alternative candidate |
| unverified primitive | lower route to local experiment only | require proof/promotion |

Policy:

```text
Registered RemixSurface is the repair authority.
LLM repair is candidate-only and must re-enter the compiler.
```

### E. Runtime Routes

The same PlanLock should be able to lower into different physical runtimes over time.

| Runtime | Use |
| --- | --- |
| local deterministic runner | proofs, tests, first implementation |
| Temporal | durable application workflows, retries, human-in-loop |
| Argo/Kubernetes Jobs | containerized DAGs and artifact-heavy work |
| Cloud Run Jobs / ECS tasks | bounded container jobs |
| Celery/Dramatiq | Python worker pools for leaf activities |
| Lambda/cloud functions | small stateless triggers and checks |
| Dagster/Flyte | typed asset/data lineage |
| ComfyUI-like node graph | media generation graph execution |

Policy:

```text
Local runner comes first.
Physical runtime emitters come after PlanLock and ledger behavior are stable.
```

## Least-Token-First Planning Cascade

The planner/router should try routes in this order.

### Route 0: Promoted Composite Reuse

No LLM required.

```text
intent -> exact/promoted composite match -> PlanLock
```

Use when a promoted pipeline or composite primitive already satisfies the request.

### Route 1: Deterministic Template Fill

No LLM required.

```text
intent -> deterministic search -> one candidate per slot -> compiler
```

Use when search returns unambiguous slot candidates and all contracts fit.

### Route 2: Compact Alias PlanDelta

Minimum LLM.

```text
CandidateBundle(planning view)
  -> LLM dense or pairs PlanDelta
  -> compiler
```

Use when candidate selection is ambiguous but source/code is not needed.

### Route 3: Deterministic Remix Repair

No new LLM if a registered mutation solves the compiler diagnostic.

```text
compiler diagnostic
  -> RemixSurface
  -> VariationRecord
  -> recompile
```

Use for scalar/list mismatch, field mismatch, output envelope, artifact conversion, retry/cache wrappers.

### Route 4: Patch PlanDelta

Targeted LLM repair.

```text
compiler diagnostic + compact candidate subset
  -> LLM patch PlanDelta
  -> compiler
```

Use when deterministic remix fails but candidate alternatives exist.

### Route 5: Evidence View Replan

Richer LLM context.

```text
CandidateBundle(evidence profile)
  -> LLM pairs PlanDelta
  -> compiler
```

Use when trust/proof/cost/history matters for choosing among candidates.

### Route 6: Gap Declaration

Do not generate code yet.

```text
LLM or compiler declares missing capability/remix
  -> gap record
  -> search broader corpus
  -> local experiment or backlog
```

Use when no verified primitive/remix can satisfy the slot.

### Route 7: Generated Adapter Candidate

Nondeterministic generation allowed, still candidate-only.

```text
gap -> narrow adapter generation -> proof fixture -> candidate primitive/variation
```

Use only for missing adapters or small bounded transformations.

### Route 8: Source-Level Review/Rewrite

Last resort.

```text
source context -> LLM/codegen -> candidate source diff -> static checks -> proof -> promotion
```

Use only when object-level or adapter-level mutation cannot solve the problem.

### Route 9: Human Review

For high-risk decisions, side effects, policy exceptions, production promotion, or unclear proof.

## Route Selection Score

A route should minimize total expected cost while satisfying safety constraints.

```text
route_score =
  estimated_input_tokens
  + estimated_output_tokens
  + compile_failure_penalty
  + repair_penalty
  + proof_debt_penalty
  + runtime_risk_penalty
  + human_review_penalty
```

Hard constraints override score:

```text
forbidden side effect -> reject
untrusted primitive in production -> reject
secret value in state/logs -> reject
large bytes inline -> reject or force ArtifactRef
missing required gate -> reject or insert verified gate
```

## Route State Machine

```text
start
  -> promoted_composite?
  -> deterministic_template_fill?
  -> compact_llm_plandelta?
  -> compile
       ok -> planlock
       repairable -> deterministic_remix
       alternative_needed -> patch_plandelta
       context_needed -> evidence_view_replan
       gap -> gap_record
  -> proof
       pass -> candidate execution or promotion review
       fail -> negative memory + route fallback
```

## CandidateBundle Contract

CandidateBundle is the LLM/search boundary.

It should include:

```text
bundle_id
registry_snapshot
template aliases
slot aliases
candidate aliases
remix aliases
known successful chains
negative memory
view profile
token estimate
```

It must support:

```text
render(profile)
resolve_plan_delta(delta)
explain_alias(alias)
hash()
```

The LLM may only refer to aliases inside the bundle. The compiler expands aliases into canonical records.

## Architecture Variant Registry

Each route/format should be registry-backed, not hidden in prose.

Minimum fields:

```yaml
route_id: llm.compact_alias_dense
route_family: llm_planning
status: candidate
serves_truth: false
input_profile: planning
output_profile: dense_plandelta
requires:
  - candidate_bundle
  - fixed_slot_order
forbidden_when:
  - variable_branch_count
  - unresolved_template_slots
fallbacks:
  - llm.compact_alias_pairs
  - llm.evidence_pairs
metrics:
  - input_tokens
  - output_tokens
  - compile_success
  - repair_count
proof:
  checker: _repos/shared-backend-components/scripts/check_teleon_pipeline_template_adversarial_benchmark.py
```

This lets Teleon carry multiple architectures at once and choose among them by policy and benchmark data.

## Benchmark Matrix

Use the same business workflow across all variants:

```text
vendor invoice review
  -> normalize invoice
  -> validate required fields
  -> score risk
  -> emit review packet
```

Authoring routes:

```text
verbose_json_steps
compact_json_ids
callable_list
primitive_handle_list
object_graph_matrix
opt_in_object_graph
object_first_pipeline
function_preserving_decorator
template_class_fill
```

LLM routes:

```text
alias_only_dense
signature_dense
planning_dense
planning_pairs
evidence_pairs
patch_only
gap_only
```

Failure cases:

```text
unknown primitive alias
invalid state root
arbitrary object crawl attempt
scalar primitive selected for list slot
side effect before required gate
large bytes returned inline
secret value returned into state
missing proof for production route
```

Metrics:

```text
authoring_surface_token_proxy
llm_input_tokens
llm_output_tokens
compiled_step_token_proxy
planlock_size
compile_success
execution_success
semantic_output_digest
deterministic_digest_count
runtime_ns
repair_success
malformed_rejection
proof_obligations_generated
developer_readability_score
```

## Formalization Rules

Do not freeze a route as preferred until it has:

```text
versioned route id
declared input/output profiles
declared preconditions
declared fallback route
focused benchmark coverage
malformed rejection coverage
PlanLock compatibility
serves_truth=false unless promoted
```

Do not remove a route unless:

```text
it has no unique usage lane
it loses benchmarks across its lane
it has a replacement with equal or better compile success
old PlanLocks remain executable or have explicit migration
```

## Next Implementation Slices

### 1. Route Registry v0

Create machine-readable route records for:

```text
promoted_composite
deterministic_template_fill
compact_alias_dense
compact_alias_pairs
patch_plandelta
evidence_replan
deterministic_remix
generated_adapter_candidate
source_rewrite_candidate
human_review
```

### 2. CandidateBundle v0

Implement bundle rendering, alias resolution, and token estimates.

### 3. ViewProfile v0

Implement:

```text
alias_only
signature
planning
evidence
debug
canonical
```

### 4. PlanDelta Profiles

Implement:

```text
dense
pairs
patch
gap
```

### 5. Benchmark Expansion

Extend the adversarial benchmark so every route records:

```text
token proxy
compile result
semantic digest
fallback taken
proof obligation output
```

### 6. Function-Preserving Python Authoring

Add the `P(fn)` route beside the current object-returning `@primitive` route.

### 7. RemixSurface v0

Implement three deterministic remixes:

```text
map_sequence
field_rename
output_wrapper
```

Each must emit a `VariationRecord`.

## Final Position

Teleon should not bet on one architecture surface. It should carry a portfolio of compatible routes:

```text
deterministic routes first
least-token LLM routes second
richer LLM routes only when needed
generated adapters only for real gaps
source rewrite as last resort
human review for high-risk edges
```

The platform advantage is not that one syntax wins. The advantage is that every route compiles through the
same canonical records, deterministic compiler, PlanLock, ledger, and proof/promotion boundary.

