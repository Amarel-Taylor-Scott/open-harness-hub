---
license: MIT
tags:
- evaluation
- experimental
- media
- media-claims-factcheck
- media.factcheck
- open-harness-hub
- retrieval
- synthetic-expansion
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- media
- media.factcheck
---

# Media Claims Factcheck review harness

<!-- Generated from Open Harness Hub manifest `harness/media-claims-factcheck-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness that combines persona, grep flags, RAG grounding, and judge scoring for media claims factcheck packets.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: media, media.factcheck
**Capabilities**: evaluation, retrieval, verification
**Modalities**: text
**Trust boundary**: local
## Privacy boundaries

- **raw_input**: Raw packet remains local unless the deployment explicitly configures an external model adapter.
- **derived_output**: Findings may contain sensitive operational details; publish only redacted summaries.
- **external_calls**: No external calls are required by the harness.

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
@misc{media-claims-factcheck-review_open_harness_hub,
  title  = {Media Claims Factcheck review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/media-claims-factcheck-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/media-claims-factcheck-review`.
