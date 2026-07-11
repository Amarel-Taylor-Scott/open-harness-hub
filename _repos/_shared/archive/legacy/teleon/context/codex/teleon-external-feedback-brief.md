# Teleon External Feedback Brief

This document is a paste-ready architecture brief for getting adversarial feedback from Claude, GPT, or
another strong online model. It is intentionally self-contained: assume the reviewer has no repository
access.

The request is not "validate that this is good." The request is: find weak assumptions, simpler designs,
more token-efficient representations, more Pythonic object models, better deterministic compiler patterns,
and failure modes that this architecture might miss.

## Feedback Prompt

Please review the architecture below as a senior systems/compiler/runtime engineer. Be adversarial. I am
building a platform where a large corpus of Python/code primitives can be searched, combined, mutated,
compiled, executed, and promoted with minimal LLM token usage.

I want feedback on:

1. Whether the object-first Python authoring layer is the right direction.
2. Whether the boundary formats are standardized enough.
3. Whether the LLM context/output formats are close to minimum-token without becoming fragile.
4. Whether the deterministic compiler/runtime model is robust enough.
5. Whether the memory/storage/logging model covers real workloads.
6. Whether the proof/promotion boundary is strong enough.
7. Whether there are simpler, more Pythonic, or more scalable alternatives.
8. What should be benchmarked before formalizing these contracts.

Please separate:

- likely-good design choices;
- risky design choices;
- missing abstractions;
- over-engineered pieces;
- token-efficiency improvements;
- Python ergonomics improvements;
- determinism/security/replay failure modes;
- concrete next experiments.

Do not assume the LLM should write code at runtime. The preferred model is:

```text
human intent
  -> primitive/template search
  -> compact LLM plan or patch only when needed
  -> deterministic compiler validates, mutates, orders, and locks
  -> runtime executes locked plan
  -> ledger/proofs record reality
  -> promotion decides what can serve truth
```

## Core Thesis

The system is not just RAG over code. It is a component-graph compiler and runtime.

The LLM should mostly see compact primitive records:

```text
purpose
inputs
outputs
side effects
memory policy
cache policy
runtime compatibility
graph neighbors
mutation/remix affordances
proof status
trust status
```

The LLM should mostly output:

```text
template choice
slot bindings
candidate primitive aliases
requested deterministic mutations/remixes
unresolved gaps
assumptions
```

The LLM should not normally read full source code, rewrite primitive source, enqueue arbitrary tasks, or
execute runtime actions.

## Product And Infrastructure Context

The repo contains an AI Done Right product family with several surfaces:

- Teleon: purpose-driven, eval-gated, self-adaptive compute runtime.
- Baltor: verified/provable context layer powered by Teleon.
- OpenHubForAI/Open Harness Hub: open registry of components, harnesses, rule packs, knowledge packs,
  adapters, tools, rubrics, benchmarks, and pipelines.
- AIDevObserver: review/coaching layer for how teams use AI coding agents.

The open ecosystem layer standardizes modular AI-system pieces. Catalog entries are YAML definitions
validated against JSON Schemas. The taxonomy is industry-agnostic: industry-specific concepts should be
leaf instances of generic component types, not top-level taxonomy entries.

Important repo laws:

- No magic values: shared constants, paths, counts, IDs, and thresholds should have one owner.
- Pipelines do not wire raw rule packs directly to models; rule packs travel through harnesses.
- Volatile facts belong in tools or knowledge packs, not personas.
- Reproducibility is first-class.
- Privacy boundaries travel with components.
- Candidate artifacts do not serve truth until proof/promotion.

## Existing Layers

### 1. AI-First Python Naming

The codebase uses an AI-first naming convention for owned Python symbols:

```text
py_<kind>__<file>__<scope>__<name>
```

Example shape:

```text
py_function_src_teleon_registry_primitive_match__semantic_text
py_arg_src_teleon_registry_primitive_match__semantic_text__record
```

The purpose is that a deterministic graph tool or LLM can infer kind, file, scope, and meaning from the
symbol itself. It is intentionally grepable and graphable.

This naming layer is not the whole contract. The registry contract still owns type surfaces, side effects,
memory, cache, policy, proof, and promotion status.

### 2. Deterministic Python Graph Layer

The Python analyzer is AST-based, not LLM-based. It tracks:

- definitions;
- references;
- imports;
- calls;
- inheritance;
- containment;
- locals;
- args;
- vars;
- operation-level nodes.

The intended graph layers are:

```text
symbol graph:
  class/function/method/var/arg/local nodes

structure graph:
  contains/calls/inherits/uses edges

operation graph:
  assign/compare/binop/call/return/branch/loop nodes

future deeper graph:
  branch-aware control flow and interprocedural data flow
```

This graph is deterministic evidence. LLM review is optional enrichment, not truth.

### 3. Primitive Registry And Hybrid Search

The registry should not expose raw source by default. It should expose normalized primitive records and
compact generated views.

Search should combine:

- exact IDs;
- pyprefix names;
- keywords;
- labels/tags;
- input contracts;
- output contracts;
- graph neighbors;
- mutation hints;
- semantic embeddings;
- successful historical chains;
- failure/negative memory.

The matcher should classify candidates as:

```text
exact_match
deterministic_edit_match
nondeterministic_edit_match
incompatible
```

### 4. Deterministic Mutation / Remix Layer

If a primitive is close, deterministic mutation should be tried before LLM source rewrite.

Examples:

```text
scalar_to_sequence.map
sequence_to_scalar.aggregate
field_rename_adapter
field_projection_adapter
output_field_wrapper
input_envelope_wrapper
type_alias_adapter
unit_conversion_adapter
artifact_materialize_adapter
artifact_reference_adapter
retry_wrapper
cache_wrapper
rate_limit_wrapper
idempotency_wrapper
provenance_wrapper
validation_gate_inserter
side_effect_saga_wrapper
batch_chunking_adapter
stream_to_batch_adapter
batch_to_stream_adapter
local_api_implementation_swap
browser_to_deterministic_extractor
model_cost_downshift
generated_adapter_candidate
```

Every mutation/remix should declare:

```text
id
preconditions
contract delta
side-effect delta
memory impact
cache impact
runtime impact
proof obligations
rollback/invalidation behavior
promotion requirements
```

### 5. Pipeline Template Runtime

The runtime supports one primitive step per line, but not as uncontrolled imperative glue.

The current lower-level runtime supports:

```text
primitive_step
primitive_metadata
primitive_handle
callable_surface
primitive_id_from_callable
primitive_signature_contract
primitive_record_from_callable
compact_llm_view_from_primitive_record
flatten_primitive_object_graph
handles_from_primitive_object_graph
pipeline_template_from_primitives
compile_pipeline_template_from_primitives
pipeline_template_from_object_graph
compile_pipeline_template_from_object_graph
execute_compiled_pipeline_template
```

State-passing modes:

```text
task_value     # primitive receives whole task and returns next task
task_patch     # primitive receives whole task and returns dict patch
named_inputs   # primitive receives explicit kwargs from allowed state paths
```

Output storage modes:

```text
inline
artifact_ref
```

Allowed state roots:

```text
$task
$context
$nodes
$system
```

The runtime compiles templates against an allowed callable registry. It rejects primitive IDs outside that
registry. It logs JSON-safe candidate events. It uses bounded retry loops. It remains candidate-only until
proof/promotion.

### 6. Object-First Python Facade

The newer direction is: objects inside Python, standardized strings/JSON at boundaries.

Python authors should not hand-type primitive IDs and step labels everywhere. Local Python should use real
objects, then deterministically serialize them.

Example:

```python
from src.teleon.synthesis.pipeline_object_api import primitive


@primitive(state_mode="task_patch")
def normalize(task: dict) -> dict:
    return {"name": task["name"].strip()}


@primitive(state_mode="task_patch")
def validate(task: dict) -> dict:
    return {"is_valid": bool(task["name"])}


flow = normalize >> validate
compiled = flow.compile("example")
result = flow.run({"name": "  vendor  "})
```

The facade exposes:

```text
Primitive
Pipeline
primitive decorator
pipeline constructor
discover_primitives(namespace)
compact_alias_lines(primitives)
operator composition with >>
```

This facade should not become a second runtime. It should emit the same deterministic primitive handles,
step specs, compact views, and candidate-only compiled plans as the lower-level runtime.

### 7. Object Graph Authoring

Because Python functions, handles, lists, tuples, dicts, classes, and objects are all objects, Python can
represent pipeline structure naturally:

```python
flow = [
    acquire,
    [parse_html, parse_pdf],
    normalize,
    validate,
    emit,
]
```

or:

```python
flow = {
    "intake": [normalize, validate],
    "review": [[score, emit]],
}
```

The compiler may flatten explicit containers and opt-in objects. It should preserve `structure_path` on
each emitted step. It should not crawl arbitrary object internals.

Opt-in object pattern:

```python
class InvoiceReviewFlow:
    def to_teleon_primitives(self):
        return {
            "intake": [normalize, validate],
            "review": [score, emit],
        }
```

### 8. Compact LLM Views And Boundary Formats

The system should use multiple generated views from one canonical object/record model.

```text
Python object
  -> canonical primitive record
  -> compact LLM view
  -> search index row
  -> PlanDelta aliases
  -> PlanLock node
  -> ledger events
```

Strings are not bad. Unstandardized strings are bad.

Objects are not automatically token-efficient. Objects become useful when they generate standardized,
compact, parseable strings.

Recommended boundary principle:

```text
Python authoring: object references
LLM input: compact line records with local aliases
LLM output: compact schema-constrained JSON
compiler input: expanded canonical records and objects
runtime input: PlanLock / compiled step specs
ledger: JSONL events and hashes
```

Example compact candidate line:

```text
P0 normalize task>dict mode:task_patch storage:inline truth:0
```

More general grammar:

```text
C<slot>.<idx> <label> <input>><output> fx:<effects> mem:<memory> c:<cache> rt:<runtime> tools:<tools> tr:<trust>
S<idx> <role> <input>><output> req:<requirements> allow:<tools>
R<slot>.<candidate>.<idx> <tool> <from_contract>=> <to_contract> proof:<obligations>
```

Compact PlanDelta output:

```json
{"v":1,"t":0,"b":[[0,0],[1,0],[2,0]],"r":[[2,0,"map"]],"g":[]}
```

Verbose PlanLock node:

```json
{
  "node": "normalize",
  "primitive_id": "py.fn:src.example.normalize:normalize@1",
  "variation": "mut:core:map@1",
  "input_bindings": {"x": "$state.raw"},
  "output_bindings": {"y": "$state.normalized"},
  "effects": [],
  "memory": "inline",
  "cache": "content_hash"
}
```

### 9. Memory, Storage, And Passing Values Between Primitives

The runtime should not pass every value through one giant task object forever.

Recommended lanes:

```text
small scalar/string/bool/int:
  inline state

small structured JSON:
  inline state or JSON artifact, depending on size

large JSON/table:
  ArtifactRef

image/video/audio/PDF/HTML/browser trace/source tree/proof log:
  ArtifactRef

secret:
  SecretRef only; never copied into state or logs

temporary local value:
  scratch/ephemeral state with TTL

side-effect result:
  receipt object plus ledger event
```

ArtifactRef shape:

```json
{
  "uri": "s3://... or file://...",
  "sha256": "...",
  "size_bytes": 123,
  "kind": "image|video|json|table|source|proof_log",
  "media_type": "application/json",
  "metadata": {}
}
```

Core stores:

```text
StateStore       small state snapshots
ArtifactStore    immutable content-addressed blobs
LedgerStore      append-only JSONL events
CacheStore       reusable primitive outputs
PlanLockStore    compiled executable plans
ProofStore       proof commands, logs, artifacts
RegistryStore    primitive/template/mutation records
GraphStore       edges, compatibility, common chains
```

### 10. Logging And Ledger

Every step attempt should emit structured JSON events.

Minimum event fields:

```text
event_index
run_id
step_id
primitive_id
attempt
status
input_digest
output_digest
error
serves_truth
```

Example:

```json
{
  "event": "primitive_step",
  "event_index": 3,
  "run_id": "run_abc",
  "step_id": "normalize",
  "primitive_id": "py.fn:src.example.normalize:normalize@1",
  "attempt": 1,
  "status": "ok",
  "input_digest": "sha256:...",
  "output_digest": "sha256:...",
  "error": null,
  "serves_truth": false
}
```

Logs are evidence, not served truth.

### 11. Compiler Responsibility

The compiler should own:

```text
schema validation
primitive existence
candidate-set membership
version resolution
input/output contract compatibility
mutation/remix applicability
side-effect ordering
gate ordering
runtime compatibility
memory policy compatibility
cache policy compatibility
secret reference safety
artifact reference policy
branch convergence
map/reduce type alignment
bounded retry legality
compensating action requirements
proof requirements
topological ordering
PlanLock emission
```

The executor runs the lockfile / compiled plan, not the LLM response.

### 12. Candidate / Promotion Boundary

Search results, compact views, generated records, object-facade outputs, LLM plans, mutations, and compiled
templates are candidate evidence by default.

Rule:

```text
serves_truth=false until proof, provenance, logs, contracts, graph edges, and promotion review pass.
```

Promotion stages can be:

```text
raw_component
indexed_component
typed_component
tested_component
approved_component
production_component
deprecated_component
```

Nondeterministic output can propose:

```text
new compact view
new plan patch
new mutation
new adapter
new primitive
new pipeline config
new explanation
```

But it should not serve truth until deterministic proof/promotion.

## Current Benchmark Direction

The current adversarial benchmark direction is to compare authoring surfaces on the same local business
workflow, such as vendor invoice review:

```text
normalize invoice
validate required fields
score risk
emit review packet
```

Authoring variants to compare:

```text
verbose_json_steps
compact_json_ids
callable_list
primitive_handle_list
object_graph_matrix
opt_in_object_graph
object_first_pipeline
```

Metrics:

```text
planner_payload_token_proxy
authoring_surface_token_proxy
compiled_step_token_proxy
deterministic_digest_count
semantic_output_digest
runtime_ns
compile_success
execution_success
repair_attempts
malformed_input_rejection
flexibility_score
```

The rule should be best-by-usage-lane, not one universal winner:

```text
LLM boundary with minimum tokens:
  compact aliases / compact JSON

local Python readability:
  object-first Primitive/Pipeline or callable list

explicit Python control:
  primitive handles

grouped composition:
  object graph / matrix

domain bundle authoring:
  opt-in objects

lockfile/debug/audit:
  verbose compiled step specs
```

## Open Design Questions

Please review these specifically.

### Python Object Model

1. Should `@primitive` return a `Primitive` object directly, or should it leave the function callable and
   attach metadata only?
2. Is `normalize >> validate >> emit` a good composition surface, or too magical?
3. Should `Pipeline` be immutable/frozen?
4. Should `Primitive` preserve function attributes such as `__name__`, `__doc__`, and `__signature__` via
   wrapper behavior?
5. Should typed slot/template classes use descriptors so slot names are captured by Python?
6. Should state paths be objects/lenses instead of strings like `$task.foo`?
7. Should mutation/remix tools be methods (`primitive.map()`) or external objects
   (`Map.apply(primitive)`)?
8. Should Python object identity ever be used for matching, or only canonical IDs?
9. How should generated/derived IDs survive refactors and file moves?
10. How should public compatibility aliases work with the pyprefix naming law?

### Standardized String Formats

1. What canonical ID grammar is best?
2. Should canonical primitive IDs include location, semantic name, content hash, registry UUID, or all of
   them?
3. Should LLM aliases be numeric (`C3.0`) or mnemonic (`normalize_0`)?
4. Should compact LLM input be line grammar, compact JSON, MessagePack-like text, or another grammar?
5. Should compact LLM output use short keys, or is readability worth the extra tokens?
6. How much schema-constrained compact JSON can be shortened before model error rates rise?
7. How should prompt caching affect the chosen format?

### Compiler / Runtime

1. Should the deterministic compiler infer missing edges, or require all bindings?
2. Should the compiler insert deterministic mutations automatically?
3. Should it preserve LLM-proposed ordering when valid, or always derive order?
4. How should loops, branches, maps, reduces, and sagas be represented in the IR?
5. Should PlanLock be canonical JSON, Protobuf, SQLite rows, or content-addressed files?
6. Should local execution and Temporal/Argo/Celery emitters share one physical-plan format?
7. What replay guarantees are realistic in Python when primitives can call arbitrary code?

### Memory / Storage

1. Is the `task/context/nodes/system/artifacts/events` state split enough?
2. Should scratch/ephemeral state be explicit?
3. Should every primitive declare a maximum inline output size?
4. Should ArtifactRef be mandatory for any bytes-like object?
5. How should streaming primitives be represented without breaking replay?
6. How should secrets be referenced and redacted deterministically?

### Proof / Promotion

1. What is the minimum proof required for a primitive to be used in auto-compiled plans?
2. Which mutations can preserve existing proofs, and which must invalidate them?
3. Should promotion be per primitive, per variation, per pipeline, or all three?
4. How should flaky proofs affect trust and retrieval ranking?
5. Should LLM explanations ever affect promotion, or only human review/proof artifacts?

### Token Efficiency

1. What is the likely lowest-token LLM input representation that remains robust?
2. What fields have the highest planning value per token?
3. Should examples be omitted by default and retrieved only when ambiguity remains?
4. Should graph neighbors be shown to the model, or only successful chain IDs?
5. Should the model receive mutation routes directly, or should the compiler hold them back for repair?
6. What benchmark would prove object-first Python plus generated compact views is better than direct
   compact JSON authoring?

## Desired End State

The desired end state is:

```text
Python objects are the authoring truth.
Canonical records are the registry truth.
Compact strings are generated views.
LLM aliases are local and temporary.
PlanDelta is compact schema-constrained JSON.
PlanLock is deterministic execution truth.
Ledger records runtime reality.
Proof/promotion decides what can serve truth.
```

The system should support:

```text
deterministic-first operation
nondeterministic candidate generation only when needed
cheap deterministic mutation before source rewrite
object-level mutation before source-level edit
compact LLM planning context
strict compiler validation
runtime lockfiles
structured JSON logs
artifact references for large data
proof-gated promotion
benchmark-driven format choices
```

## Feedback Requested

Please propose:

1. A simpler architecture if this is overbuilt.
2. A more Pythonic authoring API if the object facade is awkward.
3. A more token-efficient LLM input/output grammar.
4. A stronger canonical ID and versioning scheme.
5. A better mutation/remix contract.
6. A better state/artifact/logging model.
7. A minimal benchmark suite to decide among variants.
8. The top five failure modes that could make this system unreliable at scale.
9. The top five implementation slices to build next.

