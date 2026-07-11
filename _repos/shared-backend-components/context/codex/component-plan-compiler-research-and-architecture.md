# Teleon ComponentPlan compiler — research-backed architecture

Teleon's core bet is not "LLM writes more code." It is:

```text
intent -> retrieved ComponentCards -> constrained PipelinePlan -> deterministic compiler -> locked plan
```

The LLM should spend tokens selecting and explaining primitives, not rewriting solved loops, scrapers,
adapters, loggers, retries, queues, or API clients. The deterministic layer resolves versions, checks
I/O, enforces policy, orders nodes, emits runtime manifests, and records provenance.

That does **not** mean the platform is deterministic-only. The correct model is **deterministic-first,
nondeterministic-when-needed, candidate-until-proven**:

```text
intent
  -> deterministic retrieval / graph / contract checks
  -> deterministic adapters and mutations when available
  -> nondeterministic planning or code/edit generation only for unresolved gaps
  -> generated variant stays candidate-only
  -> deterministic proof + provenance + promotion decide whether it becomes reusable
```

Compact LLM views, enrichment summaries, mutation proposals, and pipeline configs can all have both
lanes. A deterministic tool can generate or validate them from source/graph evidence. An LLM can enrich,
rank, explain, or propose a missing variant. The trust boundary is not "was an LLM involved"; it is
whether the resulting artifact has contracts, proof, provenance, graph edges, logs, and promotion status.

## Research Pattern

The adjacent research consistently points to the same shape:

- **LLM as controller over existing tools/models.** HuggingGPT uses an LLM to plan tasks, select models by
  function descriptions, execute subtasks, and summarize results. Teleon adopts the controller idea but
  replaces free-form execution with a validator/compiler over registered primitives.
- **Generated programs as composition plans.** VISPROG and ViperGPT show LLMs composing modular visual
  functions/programs instead of relying on one end-to-end model. Code as Policies applies the same idea to
  robot primitive APIs. Teleon adopts compositional planning but makes the output a constrained graph IR,
  not arbitrary Python.
- **Video planning by structured intermediate plans.** VideoDirectorGPT uses an LLM to expand prompts into
  a video plan containing scenes, entities, layouts, backgrounds, and consistency groupings before a
  downstream generator runs. Teleon's equivalent is a capability plan with primitive nodes, input/output
  bindings, guardrails, and runtime constraints.
- **API/tool retrieval reduces hallucinated calls.** Gorilla and ToolLLM show the importance of retrieval
  over API/tool metadata. Teleon applies this to code primitives: retrieve compact ComponentCards first,
  then constrain the planner to those cards.
- **DAG/function-call compilation reduces cost and latency.** LLMCompiler frames function calls as a
  graph that can be scheduled in parallel. Teleon's compiler similarly derives topological order and can
  later emit Temporal/Argo/Celery/Cloud Run manifests.

Useful implementation ecosystems map cleanly onto Teleon's layers:

- **Backstage** informs the catalog model: components, APIs, resources, systems, templates, ownership,
  visibility, and scaffolding.
- **Haystack pipelines** validate the idea of directed multigraphs of components with explicit
  input/output connections, loops, branches, serialization, and pre-run validation.
- **Temporal** provides the replay discipline: workflow code must make the same decisions from recorded
  history; external calls belong in activities whose results are recorded.
- **CUE** informs constraint combination and schema unification across component cards, plans, runtime
  manifests, and environment config.
- **OPA/Rego** is the policy lane for side effects, licenses, runtimes, trust levels, approvals, and data
  boundaries.

## Teleon IR Layers

Use three levels, never one blob:

1. **IntentPlan** — user/LLM-readable goal, constraints, guardrails, and runtime preferences.
2. **LogicalPipelinePlan** — graph of component ids, node ids, purposes, bindings, gates, and side-effect
   declarations. The LLM may propose this, but only from retrieved candidates.
3. **PhysicalExecutionPlan / lockfile** — deterministic compiler output: resolved versions, ordered
   nodes, source digests, runtime target, seed strategy, policy report, and registry snapshot.

The executor runs the lockfile, not the LLM response.

## ComponentCard

Every primitive should eventually normalize to a ComponentCard:

```yaml
component_id: image.generate.api
version: 1.4.2
purpose: Generate an image from a normalized prompt using an approved provider.
input_contract: {shape: object, fields: {prompt: PromptSpec, seed: int}}
output_contract: {shape: object, fields: {image: ImageArtifact, provider_response: object}}
runtime: {compatible: [temporal_activity, cloud_run_job], recommended: temporal_activity}
policy: {requires_after: [prompt.normalize], requires_before_side_effect: [image_safety_gate]}
proofs: [unit, replay_smoke]
logs_schema: {event: primitive_run}
source_sha256: "..."
serves_truth: false
```

This is what RAG retrieves. The LLM should not need the full source for ordinary planning.

## PipelinePlan

The LLM output should be a strict object:

```yaml
plan_id: pinterest_image_pipeline_candidate
goal: generate_vetted_pinterest_image
nodes:
  - id: prompt_prepare
    component: prompt.prepare@2.1.0
    bindings:
      prompt: "$task.prompt"
  - id: image_generate
    component: image.generate.api@1.4.2
    bindings:
      prompt: "$nodes.prompt_prepare.outputs.normalized_prompt"
      seed: "$system.seed"
  - id: image_vet
    component: image.safety_gate@3.0.0
    gate: image_safety_gate
    bindings:
      image: "$nodes.image_generate.outputs.image"
  - id: delivery_email
    component: delivery.email.send@1.5.1
    side_effect: true
    bindings:
      recipient: "$task.mail_hook_to_email"
      image: "$nodes.image_generate.outputs.image"
```

The compiler derives the final order from bindings and policy gates. The LLM's `after` hints are useful
but not authoritative.

## Deterministic Compiler

Built now: `_repos/teleon/backend/src/teleon/synthesis/component_plan_compiler.py`.

It validates:

- every ComponentCard has required contract fields and `serves_truth=false`;
- every selected component exists and can be restricted to the retrieved candidate set;
- requested versions match available cards;
- bindings use allowed roots: `$task`, `$system`, `$nodes`;
- bound input fields are declared by the target component;
- node-output bindings create dependency edges;
- side-effect nodes are ordered after required gates;
- the graph is topologically sortable;
- the returned lockfile has immutable fields and remains candidate-only.

It emits:

- `execution_plan_id`;
- `pipeline_name`;
- `compiler_version`;
- `ordered_nodes`;
- `locked_components`;
- `component_registry_snapshot`;
- `policy_report`;
- deterministic random seed strategy;
- `serves_truth=false`.

## Pipeline Template Runtime

Built now: `_repos/teleon/backend/src/teleon/synthesis/pipeline_templates.py`.

This is the ergonomic layer between LLM JSON and runtime execution. It keeps the actual pipeline surface
as one primitive step per line while deterministic code handles state, retries, storage, and logs.

For Python-authored templates, avoid repeating magic step labels and primitive-id strings at every call
site. Attach metadata once to the callable, then let the template compiler derive the primitive id and
collision-safe step ids:

```python
@primitive_metadata(state_mode="task_patch")
def normalize_record(task: dict) -> dict:
    """Normalize a candidate task record."""
    return {"normalized": True}

@primitive_metadata(
    state_mode="named_inputs",
    input_bindings={"record": "$task"},
    output_path="$task.validation_result",
    output_storage="artifact_ref",
)
def validate_record(record: dict) -> dict:
    """Validate a normalized task record."""
    return {"valid": bool(record.get("normalized"))}

compiled = compile_pipeline_template_from_primitives(
    "record_pipeline",
    [normalize_record, validate_record],
    "Record normalization and validation as callable-backed primitive handles.",
)
```

That produces the same JSON-compatible step specs, with step ids derived from the primitive surface and
duplicate uses receiving deterministic suffixes. The LLM-facing JSON shape still uses canonical string ids
because JSON is the wire format:

```json
{
  "step_id": "prompt_add_random_emphasis",
  "primitive_id": "prompt.add_random_emphasis.v1",
  "state_mode": "task_value",
  "input_path": "$task",
  "output_path": "$task",
  "max_attempts": 1
}
```

The deterministic compiler then resolves `primitive_id` from an allowed callable registry. The LLM never
emits a callable, import path to execute, or raw glue code.

Python can also author pipelines as explicit object graphs because functions, handles, lists, dicts, and
matrices are all objects. The runtime flattens only explicit containers and opt-in objects; it does not
crawl arbitrary object internals:

```python
compiled = compile_pipeline_template_from_object_graph(
    "record_matrix_pipeline",
    {
        "ingest": [load_record, normalize_record],
        "checks": [
            [validate_schema, validate_policy],
            [validate_runtime, validate_provenance],
        ],
        "emit": [write_candidate_receipt],
    },
    "Record pipeline expressed as a deterministic Python object graph.",
)
```

Each generated step keeps a `structure_path`, such as `$.checks[1][0]`, so the source grouping remains
auditable without hand-authored step labels.

The same callable surface can seed candidate primitive records and compact LLM views. The runtime reads
`__module__`, `__qualname__`, function name, annotations, first docstring line, and attached
`primitive_metadata`; this gives the registry a deterministic starting record before any LLM enrichment:

```text
callable object
  -> candidate primitive record
  -> compact LLM view
  -> deterministic template step
  -> compiled candidate runtime
```

Supported state patterns:

- `task_value`: primitive accepts the whole task and returns the next task.
- `task_patch`: primitive accepts the whole task and returns a dict patch merged into the task.
- `named_inputs`: primitive gets explicit keyword inputs from `$task`, `$context`, `$nodes`, or `$system`.
- `artifact_ref`: large outputs are stored by digest and only a reference is passed forward.
- `object_graph`: explicit Python containers organize primitive objects before flattening to step specs.

Every attempt emits a JSON-safe `primitive_step` event with `run_id`, `step_id`, `primitive_id`,
`attempt`, `status`, input/output digests, error text, and `serves_truth=false`.

## Schema And Template Decision

Do not make the core architecture depend on **Pydantic** or **Jinja**.

Those are useful adapters, not the center:

- **Pydantic / JSON Schema** are good at constraining LLM output and generating ordinary API-facing
  schemas. They are not enough by themselves for policy, graph reachability, side-effect sequencing,
  license/trust rules, or cross-runtime compilation.
- **CUE** is stronger for unifying constraints across component cards, plans, runtime manifests, and
  environment config. It is a good candidate for the next schema layer once the Python IR is stable.
- **OPA/Rego** is better for policy: "can this side effect run?", "is this license allowed?", "does this
  trust level require owner review?", "is this runtime permitted for this tenant?"
- **Jinja/Copier/Nunjucks** are artifact renderers. They should render from the locked IR, not decide
  semantics. If a renderer is replaced by direct AST/codegen, Go templates, Starlark, Cue export, or a
  Temporal SDK emitter, the lockfile contract should not change.

The durable core is:

```text
ComponentCard schema -> PipelinePlan schema -> deterministic graph/type/policy compiler -> lockfile
```

Everything else is pluggable. This matters for Teleon's AI-first code standard: generated adapters should
not be arbitrary template text. They should be emitted from typed nodes with pyprefix names, explicit
input/output contracts, logs schema, mutation provenance, and proof commands.

## 2026-06-28 Research Refinement

The stronger combined system is not "pick Pydantic" or "pick Jinja." It is a layered contract:

1. **Teleon IR is canonical.** ComponentCards, mutation affordances, PipelinePlans, graph edges, policy
   reports, and lockfiles are the durable objects. Libraries may validate or render them, but no library
   owns the semantics.
2. **Schema validators are interchangeable gates.** Pydantic/JSON Schema are pragmatic for LLM structured
   outputs and Python tests. CUE is a better fit for cross-file/cross-runtime constraint unification once
   the IR stabilizes. OPA/Rego is better for tenant/runtime/license/side-effect policy than either schema
   system.
3. **Renderers are dumb emitters.** Jinja, Copier, Nunjucks, Starlark, direct Python AST generation,
   Temporal SDK emitters, Argo YAML emitters, or Dagger pipelines should all consume the same locked IR.
   If swapping the renderer changes validation, the boundary is wrong.
4. **Primitive call surfaces are registry data.** Each primitive record needs a deterministic call surface
   for normal execution and separate mutation call surfaces for verified transformations. The LLM should
   see those surfaces as compact structured metadata, not infer them from source.
5. **Mutation is a compiler pass, not codegen by default.** A near-match primitive should first try a
   deterministic adapter/mutation (`scalar_to_sequence`, `output_field_wrapper`, field mapping,
   retry/cache/rate-limit, model downshift, local/API swap). LLM-generated edits stay candidate-only until
   proof, logs, graph edges, and promotion review pass.
6. **Graph packets must become richer than symbols.** The next graph layer should persist operation nodes
   and def-use/data-flow edges into hybrid packets so search can answer "this primitive can be adapted by
   mutation X" and "this edit changes downstream capability Y" without asking an LLM to read the full file.
7. **Every representation can be hybrid.** PrimitiveCards, MutationCards, TemplateCapsules, compact LLM
   views, PipelineIR, PlanLocks, and promotion records can have deterministic evidence fields and
   nondeterministic candidate/enrichment fields. The compiler always prefers deterministic evidence and
   deterministic mutations first; nondeterministic output is a candidate artifact that may create a new
   primitive or pipeline config only after proof and promotion.

This preserves the benefit of long source names for LLM context while avoiding the failure mode where the
source name is the only contract. The contract lives in the registry and graph; the long pyprefix names
make source, graph, logs, and proofs line up deterministically.

## Hybrid Lanes: What Can Be Deterministic vs Nondeterministic

The table below is the operating rule for Teleon. Do not flatten these into one lane.

| Layer | Deterministic lane | Nondeterministic candidate lane | Promotion rule |
| --- | --- | --- | --- |
| PrimitiveCard | extracted from AST/import graph/signature/proofs | LLM-enriched purpose, examples, semantic labels | accepted only if contracts/proofs still match source |
| CompactLLMView | generated from canonical card fields | compressed/reworded for better retrieval/planning | can be indexed as candidate; trusted only after deterministic diff/check |
| MutationCard | known adapter with checked preconditions | proposed new adapter/source edit/pipeline variant | must record mutation kind, proof fixture, rollback, variant diff |
| TemplateCapsule | renderer emits from locked IR | LLM proposes scaffold or template improvement | candidate template until pyprefix/proof/security checks pass |
| PipelineIR | compiler-derived bindings/order/mutations | LLM proposes nodes, bindings, alternatives, assumptions | compiler may reject, repair, or lock; raw LLM plan never executes |
| PlanLock | deterministic compiler output | none executable; LLM can explain only | executor runs lockfile only |
| Registry search | exact/blocking/BM25/type/graph/semantic rerank | LLM rerank/explain/query expansion | nondeterministic scores cannot promote or execute alone |
| Promotion | proof/provenance/log/graph checks | owner/model adjudication notes | `serves_truth=true` only after deterministic gates and required approval |

This is why "make 1,000 high-trust components compiler-ready first" is only a deployment strategy, not
the core product claim. The broader 1.7M component corpus can still participate as candidate evidence:
low-trust records can be searched, clustered, enriched, and proposed, but only high-trust or freshly
proved variants can be auto-compiled into executable plans.

## Adversarial Authoring Benchmark

Do not hard-code the pipeline authoring surface to a binary choice like "JSON vs Python" or "callables vs
strings." Python's object model makes more useful surfaces possible: callable lists, explicit primitive
handles, nested lists/dicts/matrices, and opt-in domain objects that expose their primitive graph. The
right answer is usage-lane specific:

- LLM boundary with lowest tokens: compact primitive IDs or slot bindings.
- Linear Python readability: callable lists, one primitive per line.
- Explicit Python control: primitive handles when metadata overrides are needed.
- Grouped composition: object graphs built from lists, dicts, and matrices.
- Domain bundle authoring: opt-in objects with `to_teleon_primitives`.
- Lockfile/debug/audit: verbose compiled step specs.

The benchmark contract in `architecture/teleon_pipeline_template_adversarial_benchmark.json` evaluates all
of these on the same local vendor-invoice workflow. The proof checks token proxy, deterministic repeated
execution, semantic output equivalence, structure-path preservation, and malformed/adversarial rejection.
That means "best" is measured by lane rather than guessed globally. A future surface can replace an
incumbent only by being added as a named benchmark variant and passing the full proof gate.

## Object-First Python Facade

The clean Python authoring direction is object-first, not string-first. The facade in
`_repos/teleon/backend/src/teleon/synthesis/pipeline_object_api.py` lets local authors use `@primitive`, `Primitive`, `Pipeline`,
and `>>` composition while the compiler still emits the same serializable primitive handles and step specs:

```python
@primitive(state_mode="task_patch")
def normalize(task: dict) -> dict:
    return {"name": task["name"].strip()}

@primitive(state_mode="task_patch")
def validate(task: dict) -> dict:
    return {"is_valid": bool(task["name"])}

flow = normalize >> validate
compiled = flow.compile("example")
```

The facade uses Python's observable object surface: callable identity, `__module__`, `__qualname__`,
`__name__`, annotations, docstrings, and attached metadata. It can also discover primitive objects from a
namespace and generate compact standardized alias lines for LLM planning. This keeps Python ergonomic
without making Python objects the wire format. Objects are for construction; standardized strings and JSON
are generated views for LLM context, lockfiles, logs, and registry storage.

## Registry Wrapping Standard

Every primitive registry row must be understandable without source:

- `call_surface`: where/how the primitive can be invoked (`entrypoint_candidate`, source path, symbol,
  input/output shape, candidate-only boundary);
- `input_contract` and `output_contract`: machine-readable shapes and fields;
- `composition`: consumed state, produced state, invalidations, repeatability, idempotency/purity status,
  side-effect boundary, and edge policy;
- `mutation_affordances`: applicable mutation hints plus verified deterministic call surfaces;
- `proof_command`, `logs_schema`, `dependencies`, `license_provenance`, `graph_edges`;
- `serves_truth=false`.

Built now: `scripts/primitive_registry_builder.py` emits `call_surface`, `composition`, and
`mutation_affordances` into both candidate records and search rows.

Verified mutation call surfaces currently exposed by registry rows:

- `scalar_to_sequence` ->
  `src.teleon.synthesis.primitive_variations.py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation`
- `output_field_wrapper` ->
  `src.teleon.synthesis.primitive_variations.py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation`
- `linear_graph_composition` ->
  `src.teleon.synthesis.primitive_variations.py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract`
- `linear_graph_execution` ->
  `src.teleon.synthesis.primitive_variations.py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph`

Other mutation classes such as field rename, retry/cache/rate-limit, model downshift,
browser-to-deterministic extractor, and local/API swap remain candidate surfaces until their deterministic
wrappers and proofs are implemented.

## Mutation Before Regeneration

Primitive search already classifies whether a primitive is:

- exact;
- compatible through deterministic adapter/mutation;
- compatible only through generated candidate edit;
- incompatible.

The compiler should prefer deterministic adapter nodes before asking an LLM to rewrite code:

- scalar -> sequence wrapper;
- output field wrapper;
- field rename adapter;
- retry/cache/rate-limit adapter;
- model-cost downshift;
- browser/LLM scraper -> deterministic extractor;
- local/API implementation swap.

Generated code is the last resort and enters the registry only as a candidate with proof gates.

When deterministic mutation fails, the compiler should not jump straight to arbitrary full-code rewrite.
It should emit a **candidate mutation request**:

```json
{
  "kind": "generated_adapter_candidate",
  "reason": "input contract mismatch not bridged by known deterministic mutations",
  "source_primitive": "primitive.id",
  "target_contract": {"input": "...", "output": "..."},
  "required_proofs": ["contract_fixture", "replay_smoke", "side_effect_check"],
  "serves_truth": false
}
```

That request can be handled by an LLM/codegen lane, but the output is just another candidate primitive,
MutationCard, TemplateCapsule, or PipelineIR patch. It is never trusted because it was generated; it is
trusted only if the deterministic proof/promotion lane later proves it.

## Runtime Strategy

Use one logical plan, many runtime emitters:

- **Temporal** for durable application workflows, retries, idempotency, and human-in-loop.
- **Argo/Kubernetes Jobs/Cloud Run Jobs** for containerized heavy tasks and indexing.
- **Celery/Dramatiq** for Python worker pools, never as the source-of-truth planner.
- **Dagster** later when persistent assets and lineage become the dominant object.
- **Dagger/Nix/Bazel** later for reproducible build materialization.

The runtime receives a locked node spec, not a prompt:

```json
{
  "run_id": "run_001",
  "node_id": "image_generate",
  "component_id": "image.generate.api",
  "component_version": "1.4.2",
  "seed": 123456,
  "input_artifacts": {},
  "idempotency_key": "run_001:task_abc:image_generate:attempt_1"
}
```

## Source Trail

- HuggingGPT: https://arxiv.org/abs/2303.17580
- VISPROG: https://arxiv.org/abs/2211.11559
- ViperGPT: https://arxiv.org/abs/2303.08128
- VideoDirectorGPT: https://arxiv.org/abs/2309.15091
- Gorilla/APIBench: https://arxiv.org/abs/2305.15334
- ToolLLM/ToolBench: https://arxiv.org/abs/2307.16789
- LLMCompiler: https://arxiv.org/abs/2312.04511
- Code as Policies: https://arxiv.org/abs/2209.07753
- Backstage system model: https://backstage.io/docs/features/software-catalog/system-model/
- Backstage templates: https://backstage.io/docs/features/software-templates/
- Haystack pipelines: https://docs.haystack.deepset.ai/docs/pipelines
- Temporal workflows: https://docs.temporal.io/workflows
- CUE introduction: https://cuelang.org/docs/introduction/
- OPA docs: https://www.openpolicyagent.org/docs

## Load-Bearing Rule

The LLM may choose candidate components and propose bindings, but only deterministic code may validate,
order, lock, emit runtime manifests, execute, and promote.
