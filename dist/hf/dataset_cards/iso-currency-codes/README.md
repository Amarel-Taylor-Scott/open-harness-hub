---
license: CC0-1.0
tags:
- cross_industry
- currency
- finance
- iso-4217
- open-harness-hub
- retrieval
- stable
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: ISO 4217 currency codes
---

# ISO 4217 currency codes

<!-- Generated from Open Harness Hub manifest `knowledge-pack/iso-currency-codes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

ISO 4217 three-letter currency codes with name, numeric code, and
minor-unit precision. Useful for finance pipelines that need to
validate currency strings or normalize amounts. Sample subset; the
full ISO 4217 list (~180 codes) drops in here at production time.

**Industries**: finance, cross_industry
**Capabilities**: retrieval, verification
**Modalities**: text, structured
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/iso-currency-codes.jsonl` | jsonl | — |

## Provenance

- **sources**: ISO 4217 (public)
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/iso-currency-codes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{iso-currency-codes_open_harness_hub,
  title  = {ISO 4217 currency codes},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/iso-currency-codes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/iso-currency-codes`.
