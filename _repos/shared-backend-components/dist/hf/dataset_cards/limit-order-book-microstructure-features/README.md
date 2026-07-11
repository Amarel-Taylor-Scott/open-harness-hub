---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- finance
- ingestion-target
- knowledge-pack
- open-harness-hub
- regex
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Limit Order Book Microstructure Features
---

# Limit Order Book Microstructure Features

<!-- Generated from OpenHubForAI manifest `knowledge-pack/limit-order-book-microstructure-features` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: closing-auction/vol forecasting needs WAP, imbalance, spread, book pressure, realized-vol + no-leakage time Grounded in Optiver order-book/auction datasets (CC) + microstructure feature defs (quant lit) via regex retrieval. Lift: won by GBDT/NN over hand-engineered LOB features w/ leakage-safe folds (MAE); feature lib + guards = lift

**Industries**: finance, compliance
**Capabilities**: retrieval, verification
**Modalities**: structured, text
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/esoteric-packs/limit-order-book-microstructure-features.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Optiver order-book/auction datasets (CC) + microstructure feature defs (quant lit)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/limit-order-book-microstructure-features.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{limit-order-book-microstructure-features_open_harness_hub,
  title  = {Limit Order Book Microstructure Features},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/limit-order-book-microstructure-features},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/limit-order-book-microstructure-features`.
