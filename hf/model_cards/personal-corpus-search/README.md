---
license: MIT
tags:
- cross_industry
- experimental
- memory
- open-harness-hub
- personal-rag
- personal_productivity
- reasoning
- retrieval
- search
- text
library_name: open-harness-hub
pipeline_tag: text-generation
language:
- en
region:
- personal_productivity
- cross_industry
---

# Personal corpus search (RAG over user's own files / notes / docs)

<!-- Generated from Open Harness Hub manifest `harness/personal-corpus-search` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Search the user's personal corpus — their own files, notes,
emails, calendar, contacts — and return answer + citations
scoped to ONLY the user's data. Authorization-gated; refuses
to answer questions about a person from third-party data
unless the user has explicitly authorized.

Trust boundary is local — the user's data does not leave their
device unless they choose a hosted model arm.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `privacy` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: personal_productivity, cross_industry
**Capabilities**: retrieval, reasoning, memory
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### query → personal corpus retrieve → cite-first answer

1. load user preferences (incl. privacy gates)
2. scope retrieval to user's own corpus (calendar / contacts / notes / docs / emails)
3. retrieve top-K from each source (hybrid BM25 + dense)
4. rerank with cross-encoder
5. compose persona + retrieved + tool registry
6. generate answer with citations to source URIs / file paths
7. redact any third-party PII before answer is returned

## Privacy boundaries

- **raw_input**: the query stays on user's device
- **derived_output**: the answer stays with the user
- **external_calls**: only if model_target.trust_boundary == external AND user opted in via env

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `anthropic_claude` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{personal-corpus-search_open_harness_hub,
  title  = {Personal corpus search (RAG over user's own files / notes / docs)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/personal-corpus-search},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/personal-corpus-search`.
