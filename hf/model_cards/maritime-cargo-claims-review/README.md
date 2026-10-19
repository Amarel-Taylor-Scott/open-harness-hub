---
license: MIT
tags:
- evaluation
- expansion-v6
- experimental
- insurance.claims
- maritime-cargo-claims
- maritime.safety
- open-harness-hub
- retrieval
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- maritime.safety
- insurance.claims
---

# Maritime Cargo Claims review harness

<!-- Generated from Open Harness Hub manifest `harness/maritime-cargo-claims-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness for benchmarkable maritime cargo claims review using persona, grep, RAG, privacy, and reusable review processors.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: maritime.safety, insurance.claims
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
@misc{maritime-cargo-claims-review_open_harness_hub,
  title  = {Maritime Cargo Claims review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/maritime-cargo-claims-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/maritime-cargo-claims-review`.
