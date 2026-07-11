---
license: MIT
tags:
- evaluation
- experimental
- food-quality
- food.safety
- food_safety
- governance
- hold-release
- image
- label-ocr
- logistics.cold_chain
- multimodal
- open-harness-hub
- recall
- retrieval
- structured
- tabular
- temperature-log
- text
- timeseries
- verification
library_name: open-harness-hub
language:
- en
region:
- food.safety
- food_safety
- logistics.cold_chain
---

# Food quality multimodal hold-release harness

<!-- Generated from OpenHubForAI manifest `harness/food-quality-multimodal-hold-release` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Multi-model harness for food quality and safety triage that routes product photos, label OCR, lot codes, temperature logs, supplier records, complaint narratives, inspection notes, and recall or hold-release rules.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `official_sources` layer
- `rag` layer
- `classifier` layer
- `privacy` layer

**Industries**: food.safety, food_safety, logistics.cold_chain
**Capabilities**: governance, retrieval, verification, evaluation
**Modalities**: text, image, structured, tabular, timeseries, multimodal
**Trust boundary**: mixed
## Privacy boundaries

- **raw_input**: Supplier records and complaint details remain tenant-scoped.
- **derived_output**: Disposition packets may contain commercially sensitive data and require review before sharing.
- **external_calls**: Hosted OCR or vision models require redaction and approved routing.

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `label_ocr_model` | `openai_compatible` | mixed |
| `temperature_log_checker` | `callable` | local |
| `quality_disposition_model` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{food-quality-multimodal-hold-release_open_harness_hub,
  title  = {Food quality multimodal hold-release harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/food-quality-multimodal-hold-release},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/food-quality-multimodal-hold-release`.
