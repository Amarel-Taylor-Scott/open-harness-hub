---
license: MIT
tags:
- beta
- citations
- cross_industry
- dialogue
- grep
- open-harness-hub
- rag
- reasoning
- retrieval
- safety
- safety_gating
- text
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- cross_industry
---

# Text Safety Review

<!-- Generated from Open Harness Hub manifest `harness/text-safety-review` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

A general-purpose text harness that composes persona + GREP +
RAG + tools + (optional) online grounding around a model call.
Designed to produce cited, bounded, citation-first responses.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: cross_industry
**Capabilities**: safety_gating, retrieval, reasoning, dialogue
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### Prompt → grounded cited response

1. normalize chat messages
2. redact PII (via rule-pack/privacy-pii-text-en)
3. fire GREP rules; record severity hits
4. retrieve top-k RAG with BM25, optional dense, RRF merge
5. expand retrieved docs with 1-hop citation graph
6. compose persona + retrieved context + tool registry
7. call model
8. stream response + per-layer trace
9. verify every claim cited

## Privacy boundaries

- **raw_input**: stays local to the running harness process
- **derived_output**: may be synced to the hub only after anonymization gate
- **external_calls**: only when model_target.trust_boundary == 'external' AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `openai_compatible` | `openai_compatible` | external |
| `anthropic_judge` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{text-safety-review_open_harness_hub,
  title  = {Text Safety Review},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/text-safety-review},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `harness/text-safety-review`.
