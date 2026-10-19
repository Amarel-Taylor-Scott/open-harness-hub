---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- supply_chain
- trade
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Hts Classification And Add Cvd Orders
---

# Hts Classification And Add Cvd Orders

<!-- Generated from Open Harness Hub manifest `knowledge-pack/hts-classification-and-add-cvd-orders` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: fabricate 10-digit HTS suffixes; miss active AD/CVD orders, scope rulings, Section 301 rates Grounded in USITC HTS + CBP CROSS + Commerce/ITC AD/CVD (public domain) via rag_vector retrieval. Lift: GRI rule chains + fast-changing duty overlay; wrong subheading = seized goods

**Industries**: trade, supply_chain
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
| `data/esoteric-packs/hts-classification-and-add-cvd-orders.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: USITC HTS + CBP CROSS + Commerce/ITC AD/CVD (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hts-classification-and-add-cvd-orders.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hts-classification-and-add-cvd-orders_open_harness_hub,
  title  = {Hts Classification And Add Cvd Orders},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hts-classification-and-add-cvd-orders},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hts-classification-and-add-cvd-orders`.
