---
name: code-act-jupyter-loop
description: Given a natural-language goal, generate Python code → execute in Jupyter
  sandbox → observe output → iterate until the model declares the task done or max_iterations
  is hit.
when_to_use: 'Pipeline kind: code_act.'
---

# Code-act Jupyter loop

The OpenInterpreter pattern: model emits Python code in fenced
blocks, runtime renders the message + executes the code in a
Jupyter kernel, streams the observation back into the model's
context, loops until the model emits a `DONE` marker.

Verified by Open Harness Hub mining of the OpenInterpreter clone:
`interpreter/core/respond.py` implements exactly this loop.

## Task

Given a natural-language goal, generate Python code → execute in
Jupyter sandbox → observe output → iterate until the model
declares the task done or max_iterations is hit.

## Steps

1. **guard_goal** — `rule_pack` → `rule-pack/grep-cloud-secrets`
2. **loop** — `processor` → `processor/iterative-revise-loop`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/code-consultant
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-cloud-secrets`, `rule-pack/grep-ai-vendor-keys`

## Provenance

- Hub artifact: `pipeline/code-act-jupyter-loop` v0.1.0
- License: `MIT`
- Industry: ai, software
- Full source manifest: see `references/manifest.yaml`
