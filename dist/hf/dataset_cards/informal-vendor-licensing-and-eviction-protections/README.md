---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Informal Vendor Licensing And Eviction Protections
---

# Informal Vendor Licensing And Eviction Protections

<!-- Generated from OpenHubForAI manifest `knowledge-pack/informal-vendor-licensing-and-eviction-protections` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: assumes formal registration; misses municipal vending permits, trading zones, eviction/confiscation appeal Grounded in municipal vending by-laws + WIEGO + ILO R204 (reusable) via rag_vector retrieval. Lift: informal livelihoods invisible to commercial AI, hyper-local rules; confiscated-stock stakes

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
| `data/esoteric-packs/informal-vendor-licensing-and-eviction-protections.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: municipal vending by-laws + WIEGO + ILO R204 (reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/informal-vendor-licensing-and-eviction-protections.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{informal-vendor-licensing-and-eviction-protections_open_harness_hub,
  title  = {Informal Vendor Licensing And Eviction Protections},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/informal-vendor-licensing-and-eviction-protections},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/informal-vendor-licensing-and-eviction-protections`.
