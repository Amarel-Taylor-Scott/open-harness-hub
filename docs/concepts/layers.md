# Layers & primitives

Every artifact lives at one of four layers. Lower layers are the
building blocks of higher layers.

## Layer 1 - Primitives

The pure building blocks. None of them call a model or another
artifact by themselves; they describe data, behavior, or interfaces.

- **Knowledge pack** - typed bundle of *facts*.
- **Logic pack** - typed bundle of *behavior*.
- **Rule pack** - one rule family in isolation (GREP, RAG, classifier,
  heuristic, online-search, privacy, …).
- **Tool** - function-call definition (parameters + returns + side
  effects).
- **Persona** - role frame / system-prompt fragment.
- **Adapter** - provider-neutral model transport.
- **Rubric** - evaluation contract.
- **Dataset** - typed collection of inputs/outputs/labels.
- **Schema** - reusable typed I/O contract.

## Layer 2 - Harnesses

A **harness** wraps a model call (or zero - pure rule-based gates
count) with declared knowledge consumed, knowledge emitted, model
targets, input/output verification, and privacy boundaries.

A harness is the **smallest auditable unit**: a regulator can grep
`applied_layers` and see exactly which rule families fire, and
`model_targets` to see which providers the harness ever talks to.

## Layer 3 - Pipelines

A **pipeline** is a DAG of harnesses + rule packs + tools that
completes one specific task. Pipelines are the **comparable unit**:
swap one harness's model, rerun, compare the scores.

## Layer 4 - Benchmarks

A **benchmark** is a pipeline pinned to a dataset, a rubric, and a
judge. Benchmarks are the **citable unit**: anyone can reproduce a
benchmark run given `(commit_sha, dataset_version, run_date)`.
