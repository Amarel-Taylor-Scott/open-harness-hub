---
license: CC-BY-4.0
tags:
- aml
- beta
- classification
- fatf
- finance
- finance.aml
- finance.kyc
- open-harness-hub
- red-flags
- retrieval
- wolfsberg
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: AML red flags (extended)
---

# AML red flags (extended)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/aml-red-flags-extended` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Extended catalog of anti-money-laundering red flags drawn from FATF
guidance, FinCEN advisories, and Wolfsberg principles. Complements
`knowledge-pack/fatf-typologies-sample` with finer-grained
observable indicators (transaction pattern, behavioral, document,
geographic) for use in AML pipelines.

**Industries**: finance, finance.aml, finance.kyc
**Capabilities**: retrieval, classification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/aml-red-flags-extended.jsonl` | jsonl | — |

## Provenance

- **sources**: FATF Recommendations (composite), FinCEN advisories (composite), Wolfsberg AML Principles (composite)
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/aml-red-flags-extended.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{aml-red-flags-extended_open_harness_hub,
  title  = {AML red flags (extended)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/aml-red-flags-extended},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/aml-red-flags-extended`.
