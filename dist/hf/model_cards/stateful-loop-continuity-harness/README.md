---
license: MIT
tags:
- agentic-harness
- ai
- cross_industry
- evaluation
- experimental
- governance
- long-running-agents
- open-harness-hub
- prompt-loop
- serving
- software.devops
- state-loop
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

# Stateful loop continuity harness

<!-- Generated from OpenHubForAI manifest `harness/stateful-loop-continuity-harness` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness pattern for simple recurring agent execution that re-reads instruction files, updates durable state files, and stops only when explicit completion, budget, or blocked criteria are met.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `privacy` layer
- `heuristic` layer

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, serving
**Modalities**: text, structured
**Trust boundary**: local
## Privacy boundaries

- **raw_input**: Loop state remains local by default.
- **derived_output**: Summaries can be published only after removing secrets and local-only notes.
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
@misc{stateful-loop-continuity-harness_open_harness_hub,
  title  = {Stateful loop continuity harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/stateful-loop-continuity-harness},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/stateful-loop-continuity-harness`.
