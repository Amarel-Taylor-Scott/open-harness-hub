---
license: MIT
tags:
- evaluation
- experimental
- legal
- legal-ip-trademark
- legal.ip
- open-harness-hub
- retrieval
- synthetic-expansion
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- legal
- legal.ip
---

# Legal IP Trademark review harness

<!-- Generated from Open Harness Hub manifest `harness/legal-ip-trademark-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness that combines persona, grep flags, RAG grounding, and judge scoring for legal ip trademark packets.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: legal, legal.ip
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
@misc{legal-ip-trademark-review_open_harness_hub,
  title  = {Legal IP Trademark review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/legal-ip-trademark-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/legal-ip-trademark-review`.
