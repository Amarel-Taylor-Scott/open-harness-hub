---
license: MIT
tags:
- environmental.water
- evaluation
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- text
- verification
- water-main-break-response
- water_utility.sdwa
library_name: open-harness-hub
language:
- en
region:
- water_utility.sdwa
- environmental.water
---

# Water Main Break Response review harness

<!-- Generated from OpenHubForAI manifest `harness/water-main-break-response-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness for benchmarkable water main break response review using persona, grep, RAG, privacy, and reusable review processors.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: water_utility.sdwa, environmental.water
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
@misc{water-main-break-response-review_open_harness_hub,
  title  = {Water Main Break Response review harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/water-main-break-response-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/water-main-break-response-review`.
