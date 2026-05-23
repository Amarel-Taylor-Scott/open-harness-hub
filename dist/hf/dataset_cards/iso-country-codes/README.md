---
license: CC0-1.0
tags:
- country-codes
- cross_industry
- finance
- humanitarian
- iso-3166
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
pretty_name: ISO 3166 country codes (sample)
---

# ISO 3166 country codes (sample)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/iso-country-codes` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

ISO 3166-1 alpha-2, alpha-3, numeric codes plus region and a coarse
FATF risk hint. Useful for KYC, transaction-graph queries, and
cross-border-flow analysis. Sample subset; full list (~250 entries)
drops in at production time.

**Industries**: cross_industry, finance, humanitarian
**Capabilities**: retrieval, verification
**Modalities**: text, structured
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/iso-country-codes.jsonl` | jsonl | — |

## Provenance

- **sources**: ISO 3166-1 (public); FATF risk hints are illustrative.
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/iso-country-codes.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{iso-country-codes_open_harness_hub,
  title  = {ISO 3166 country codes (sample)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/iso-country-codes},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/iso-country-codes`.
