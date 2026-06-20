---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- graph
- ingestion-target
- knowledge-pack
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cross Border Remittance Corridor Compliance
---

# Cross Border Remittance Corridor Compliance

<!-- Generated from Open Harness Hub manifest `knowledge-pack/cross-border-remittance-corridor-compliance` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models don't know corridor-specific remittance limits, KYC tiers, mobile-money rules, or hawala treatment that differ per sending/receiving country pair Grounded in FATF guidance + national central-bank remittance rules + World Bank Remittance Prices (public) via graph retrieval. Lift: (corridor x rule) graph, under-documented, low-income-population focus = valley; verifiable against regulator texts

**Industries**: cross_industry
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
| `data/esoteric-packs/cross-border-remittance-corridor-compliance.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FATF guidance + national central-bank remittance rules + World Bank Remittance Prices (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cross-border-remittance-corridor-compliance.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cross-border-remittance-corridor-compliance_open_harness_hub,
  title  = {Cross Border Remittance Corridor Compliance},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cross-border-remittance-corridor-compliance},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cross-border-remittance-corridor-compliance`.
