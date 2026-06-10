---
license: CC-BY-4.0
tags:
- ai
- beta
- llm-safety
- open-harness-hub
- owasp
- retrieval
- safety_gating
- security
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: OWASP Top 10 for LLM Applications (2025)
---

# OWASP Top 10 for LLM Applications (2025)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/owasp-top-10-llm` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

OWASP Top 10 risks for LLM-based applications — prompt injection,
insecure output handling, training-data poisoning, model DoS, supply
chain, sensitive disclosure, plugin design, excessive agency,
overreliance, model theft. Used by red-team harnesses and security
evaluation pipelines.

**Industries**: security, ai
**Capabilities**: retrieval, safety_gating
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/owasp-top-10-llm.jsonl` | jsonl | — |

## Provenance

- **sources**: OWASP Top 10 for LLM Applications (https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/owasp-top-10-llm.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{owasp-top-10-llm_open_harness_hub,
  title  = {OWASP Top 10 for LLM Applications (2025)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/owasp-top-10-llm},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/owasp-top-10-llm`.
