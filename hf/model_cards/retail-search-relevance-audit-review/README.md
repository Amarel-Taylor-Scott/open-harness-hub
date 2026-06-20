---
license: MIT
tags:
- data_governance.quality
- evaluation
- expansion-v7
- experimental
- open-harness-hub
- retail-search-relevance-audit
- retail.search
- retrieval
- text
- verification
library_name: open-harness-hub
language:
- en
region:
- retail.search
- data_governance.quality
---

# Retail Search Relevance Audit review harness

<!-- Generated from Open Harness Hub manifest `harness/retail-search-relevance-audit-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Harness for benchmarkable retail search relevance audit review using persona, grep, RAG, privacy, and reusable review processors.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `privacy` layer

**Industries**: retail.search, data_governance.quality
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
@misc{retail-search-relevance-audit-review_open_harness_hub,
  title  = {Retail Search Relevance Audit review harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/retail-search-relevance-audit-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/retail-search-relevance-audit-review`.
