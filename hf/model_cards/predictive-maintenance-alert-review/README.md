---
license: MIT
tags:
- evaluation
- expansion-v7
- experimental
- manufacturing.maintenance
- open-harness-hub
- predictive-maintenance-alert
- retrieval
- sre.oncall
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- manufacturing.maintenance
- sre.oncall
---

# Predictive Maintenance Alert review harness

<!-- Generated from Open Harness Hub manifest `harness/predictive-maintenance-alert-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness for benchmarkable predictive maintenance alert review using persona, grep, RAG, privacy, and reusable review processors.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: manufacturing.maintenance, sre.oncall
**Capabilities**: evaluation, retrieval, verification
**Modalities**: text
**Trust boundary**: local
## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Findings may contain sensitive operational details and require redaction before publication.
- **external_calls**: No external calls are required by this harness.

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `review_model` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{predictive-maintenance-alert-review_open_harness_hub,
  title  = {Predictive Maintenance Alert review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/predictive-maintenance-alert-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/predictive-maintenance-alert-review`.
