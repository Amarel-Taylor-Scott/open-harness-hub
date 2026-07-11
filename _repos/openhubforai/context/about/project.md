# About the project

The OpenHubForAI is an industry-agnostic catalog of the modular
pieces of an AI-assisted system. It generalizes patterns from Taylor
Amarel's [DueCare safety ecosystem](https://github.com/Amarel-Taylor-Scott/gemma4_comp)
and the [LLM Safety Framework](https://github.com/Amarel-Taylor-Scott/llm-safety-framework).

## Goals

1. Help people **work out a benchmark** for any task.
2. Help people **work out a tool** for any task.
3. Make the substrate **portable** - any host, any database, any model.

The admission bar for every component: it must **lift capability beyond a bare
LLM** — let a model do something it cannot do reliably alone (grounded facts,
deterministic checks, retrieval, domain rules, multi-step verification). The
highest lift is in esoteric, specialized arenas where the base model is weak.
See [`_repos/_shared/codex/master-goal.md`](../../../_shared/codex/master-goal.md).

## Non-goals

- It is **not** a hosted inference provider.
- It is **not** a fork of any eval framework.
- It is **not** tied to any single industry.
- It is **not** a re-implementation of capability the model already has — if a
  frontier model does the task well zero-shot, it does not belong here.

## Contributing

PRs welcome. See the [component authoring spec](../spec/OPENHUBFORAI_SPEC.md)
(§2, the manifest envelope) for the contributor workflow.
