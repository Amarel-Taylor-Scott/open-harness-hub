---
license: MIT
tags:
- apparel-forced-labor-trace
- esg.modern_slavery
- evaluation
- expansion-v4
- experimental
- open-harness-hub
- retrieval
- supply_chain.due_diligence
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- esg.modern_slavery
- supply_chain.due_diligence
---

# Apparel Forced Labor Trace review harness

<!-- Generated from OpenHubForAI manifest `harness/apparel-forced-labor-trace-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness for apparel forced labor trace review using persona, grep, RAG, privacy, reusable processors, and benchmarkable evaluation.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: esg.modern_slavery, supply_chain.due_diligence
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
@misc{apparel-forced-labor-trace-review_open_harness_hub,
  title  = {Apparel Forced Labor Trace review harness},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/harness/apparel-forced-labor-trace-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/apparel-forced-labor-trace-review`.
