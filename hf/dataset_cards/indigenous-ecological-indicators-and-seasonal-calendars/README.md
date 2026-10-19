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
pretty_name: Indigenous Ecological Indicators And Seasonal Calendars
---

# Indigenous Ecological Indicators And Seasonal Calendars

<!-- Generated from Open Harness Hub manifest `knowledge-pack/indigenous-ecological-indicators-and-seasonal-calendars` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: lacks ILK phenological indicators, seasonal calendars, indicator species; fabricates without provenance/consent Grounded in IPBES ILK reports + FAO seasonal calendars + ethnobiology (FPIC/attribution) via rag_vector retrieval. Lift: place-specific oral tradition absent from corpora = extreme valley; adaptation/cultural-survival stakes

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
| `data/esoteric-packs/indigenous-ecological-indicators-and-seasonal-calendars.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: IPBES ILK reports + FAO seasonal calendars + ethnobiology (FPIC/attribution)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/indigenous-ecological-indicators-and-seasonal-calendars.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{indigenous-ecological-indicators-and-seasonal-calendars_open_harness_hub,
  title  = {Indigenous Ecological Indicators And Seasonal Calendars},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/indigenous-ecological-indicators-and-seasonal-calendars},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/indigenous-ecological-indicators-and-seasonal-calendars`.
