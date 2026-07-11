---
license: MIT
tags:
- agentic-harness
- ai
- codex
- cross_industry
- evaluation
- experimental
- goal-runtime
- governance
- long-running-agents
- open-harness-hub
- serving
- software.devops
- structured
- text
library_name: open-harness-hub
language:
- en
region:
- ai
- software.devops
- cross_industry
---

# Persistent goal runtime supervisor

<!-- Generated from OpenHubForAI manifest `harness/persistent-goal-runtime-supervisor` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness pattern for long-running coding-agent work where a durable goal object, completion audit, budget guard, and checkpoint log survive ordinary chat compaction and terminal restarts.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `privacy` layer
- `heuristic` layer

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, serving
**Modalities**: text, structured
**Trust boundary**: mixed
## Privacy boundaries

- **raw_input**: Goal state may include repository paths and operational details; keep local unless deployment explicitly exports traces.
- **derived_output**: Checkpoint summaries may be shared after redacting secrets, file-system-sensitive paths, and private user notes.
- **external_calls**: No external calls are required by the harness itself.

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `none` | `none` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{persistent-goal-runtime-supervisor_open_harness_hub,
  title  = {Persistent goal runtime supervisor},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/persistent-goal-runtime-supervisor},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/persistent-goal-runtime-supervisor`.
