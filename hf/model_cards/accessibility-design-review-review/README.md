---
license: MIT
tags:
- accessibility-design-review
- design_ops
- design_ops.accessibility
- evaluation
- experimental
- open-harness-hub
- retrieval
- text
- use-case-expansion
- verification
library_name: open-harness-hub
language:
- en
region:
- design_ops
- design_ops.accessibility
---

# Accessibility Design Review review harness

<!-- Generated from Open Harness Hub manifest `harness/accessibility-design-review-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Composable review harness for accessibility design review packets using persona, grep, RAG, privacy, and evaluation layers.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: design_ops, design_ops.accessibility
**Capabilities**: evaluation, retrieval, verification
**Modalities**: text
**Trust boundary**: local
## Privacy boundaries

- **raw_input**: Raw packet remains local unless deployment configures an external adapter.
- **derived_output**: Review output may contain sensitive operational details and should be redacted before publication.
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
@misc{accessibility-design-review-review_open_harness_hub,
  title  = {Accessibility Design Review review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/accessibility-design-review-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/accessibility-design-review-review`.
