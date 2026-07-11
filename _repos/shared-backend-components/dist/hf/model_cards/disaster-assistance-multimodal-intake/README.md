---
license: MIT
tags:
- disaster-assistance
- eligibility
- evaluation
- experimental
- geospatial
- governance
- government.benefits
- human-review
- humanitarian.disaster
- image
- multimodal
- open-harness-hub
- retrieval
- spatial
- structured
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- humanitarian.disaster
- government.benefits
---

# Disaster assistance multimodal intake harness

<!-- Generated from OpenHubForAI manifest `harness/disaster-assistance-multimodal-intake` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Multi-model harness for disaster assistance intake that routes forms, narratives, damage images, geospatial incident boundaries, official rules, duplicate signals, and evidence gaps to reviewable eligibility packets.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `tools` layer
- `official_sources` layer
- `rag` layer
- `classifier` layer
- `privacy` layer

**Industries**: humanitarian.disaster, government.benefits
**Capabilities**: governance, retrieval, verification, evaluation
**Modalities**: text, image, structured, spatial, multimodal
**Trust boundary**: mixed
## Privacy boundaries

- **raw_input**: Applicant evidence can contain sensitive personal and location data; default to local processing or explicit tenant approval.
- **derived_output**: Eligibility packets require role-based access and redaction before analytics or publication.
- **external_calls**: Hosted vision or text models require explicit routing policy and redaction.

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `cheap_text_reasoner` | `openai_compatible` | mixed |
| `vision_damage_classifier` | `openai_compatible` | mixed |
| `local_guard_model` | `ollama` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{disaster-assistance-multimodal-intake_open_harness_hub,
  title  = {Disaster assistance multimodal intake harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/disaster-assistance-multimodal-intake},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/disaster-assistance-multimodal-intake`.
