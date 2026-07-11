# AIDevObserver Primitive Foundry And Remixers

This note defines the practical loop for turning repeated AI-development work into reusable, edge-described primitives.

## Core Loop

```text
public/source/session signal
-> candidate capability
-> input/output edge extraction
-> blackbox behavior summary
-> deterministic tests
-> primitive record
-> mutator compatibility
-> compact search card
-> AIDevObserver route use
-> proof/promotion
```

The LLM should be used for candidate interpretation and ambiguous route design. It should not repeatedly read full source or rewrite known capabilities when a primitive edge already exists.

## Minimum Primitive Record

```text
uid
slug
input_edge
output_edge
blackbox_does
effects
memory
cpu
runtime_targets
source_ref
tests
proof_status
mutators_allowed
```

## Deterministic Mutators

Start with these because they cover many real coding-agent rebuilds:

```text
map_sequence
filter_predicate
field_rename
field_project
output_wrapper
input_envelope_wrapper
type_cast
unit_conversion
date_time_normalize
artifact_materialize
artifact_reference
cache_wrapper
retry_wrapper
idempotency_wrapper
pagination_expander
batch_chunker
fanout_fanin
schema_validator_inserter
provenance_wrapper
redaction_wrapper
```

Each mutator needs:

```text
preconditions
input_edge_before
output_edge_before
input_edge_after
output_edge_after
effect_delta
memory_delta
runtime_delta
proof_obligations
```

## Edge Adapter Families

Common adapters that avoid model codegen:

```text
scalar_to_list
list_to_scalar_first
list_to_scalar_reduce
dict_to_dataclass
dataclass_to_dict
json_body_to_validated_request
path_to_artifact_ref
bytes_to_artifact_ref
html_to_table_list
table_to_csv_artifact
table_to_parquet_artifact
model_output_to_schema_candidate
schema_candidate_to_validated_record
secret_value_to_secret_ref_blocker
side_effect_to_idempotent_effect
```

## Runtime Emitters

Runtime targets are selected after the route is compiled:

```text
local.python
container.python
k8s.job
k8s.deployment
k8s.cronjob
cloud.function.http
```

Emitters should be deterministic. Kimi/GLM can choose between viable targets when ambiguous, but YAML/handler boilerplate should be generated from templates.

## Scaling To Thousands

Use multiple source streams:

```text
local AI coding sessions
GitHub repos and examples
PyPI packages
Kaggle notebooks and competitions
Jupyter notebook code cells
n8n workflows
generic workflow/DAG JSON definitions and step lists
cloud architecture examples
public API docs
OpenAPI operation-level route contracts
framework tutorials
Markdown/MDX/RST executable snippets
shell scripts, Makefile targets, Justfile recipes, Taskfile commands
MCP server manifests and per-server bindings
StackOverflow-style repeated tasks
internal accepted AIDevObserver findings
```

For each source item:

```text
1. Extract functions, workflow steps, notebooks cells, or command sequences.
2. Normalize candidate input/output edges.
3. Cluster by blackbox behavior.
4. Keep one canonical primitive per behavior/edge.
5. Generate deterministic fixture tests.
6. Attach allowed mutators.
7. Create compact search cards.
8. Reject or quarantine low-proof candidates.
```

The target is not “many snippets.” The target is many tested, edge-compatible primitives with deterministic remix paths.
