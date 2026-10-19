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
pretty_name: Small Scale Fisheries Tenure And Gear Rules
---

# Small Scale Fisheries Tenure And Gear Rules

<!-- Generated from Open Harness Hub manifest `knowledge-pack/small-scale-fisheries-tenure-and-gear-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: industrial-fishery generalities miss SSF co-management, customary marine tenure, closed seasons, gear limits Grounded in FAO SSF Guidelines + national fisheries acts + RFB measures (reusable) via rag_vector retrieval. Lift: artisanal-fisher livelihoods low-value/low-data; food security + resource collapse stakes

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
| `data/esoteric-packs/small-scale-fisheries-tenure-and-gear-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FAO SSF Guidelines + national fisheries acts + RFB measures (reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/small-scale-fisheries-tenure-and-gear-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{small-scale-fisheries-tenure-and-gear-rules_open_harness_hub,
  title  = {Small Scale Fisheries Tenure And Gear Rules},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/small-scale-fisheries-tenure-and-gear-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/small-scale-fisheries-tenure-and-gear-rules`.
