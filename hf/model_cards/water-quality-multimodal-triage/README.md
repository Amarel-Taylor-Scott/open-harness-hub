---
license: MIT
tags:
- environmental.water
- evaluation
- experimental
- governance
- multimodal
- open-harness-hub
- public-notice
- retrieval
- sampling
- spatial
- structured
- tabular
- text
- threshold-check
- timeseries
- verification
- water-quality
- water_utility.sdwa
library_name: open-harness-hub
language:
- en
region:
- environmental.water
- water_utility.sdwa
---

# Water quality multimodal triage harness

<!-- Generated from Open Harness Hub manifest `harness/water-quality-multimodal-triage` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Multi-model harness for water quality triage that routes lab tables, sampling plans, chain-of-custody records, service-area maps, historical trends, official thresholds, and public notice drafts.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `official_sources` layer
- `rag` layer
- `classifier` layer
- `privacy` layer

**Industries**: environmental.water, water_utility.sdwa
**Capabilities**: governance, retrieval, verification, evaluation
**Modalities**: text, structured, tabular, spatial, timeseries, multimodal
**Trust boundary**: mixed
## Privacy boundaries

- **raw_input**: Operational utility data may be sensitive; keep raw tables and maps tenant-scoped.
- **derived_output**: Public notice drafts must pass legal and operator review before release.
- **external_calls**: Hosted drafting models receive only redacted, summarized findings unless explicitly approved.

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `tabular_threshold_checker` | `callable` | local |
| `notice_draft_model` | `openai_compatible` | mixed |
| `trend_summarizer` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{water-quality-multimodal-triage_open_harness_hub,
  title  = {Water quality multimodal triage harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/water-quality-multimodal-triage},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/water-quality-multimodal-triage`.
