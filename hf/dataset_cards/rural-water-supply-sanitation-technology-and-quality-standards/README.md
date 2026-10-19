---
license: CC-BY-4.0
tags:
- capability-lift
- esg
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- supply_chain
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Rural Water Supply Sanitation Technology And Quality Standards
---

# Rural Water Supply Sanitation Technology And Quality Standards

<!-- Generated from Open Harness Hub manifest `knowledge-pack/rural-water-supply-sanitation-technology-and-quality-standards` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: generic plumbing misses appropriate-tech selection, national water-quality limits, CLTS/O&M Grounded in WHO Drinking-water Quality Guidelines + national WASH + JMP ladders + CLTS (reusable) via rag_vector retrieval. Lift: rural WASH for poor communities thin data/no pull; waterborne-disease stakes

**Industries**: esg, supply_chain
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
| `data/esoteric-packs/rural-water-supply-sanitation-technology-and-quality-standards.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: WHO Drinking-water Quality Guidelines + national WASH + JMP ladders + CLTS (reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rural-water-supply-sanitation-technology-and-quality-standards.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rural-water-supply-sanitation-technology-and-quality-standards_open_harness_hub,
  title  = {Rural Water Supply Sanitation Technology And Quality Standards},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rural-water-supply-sanitation-technology-and-quality-standards},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rural-water-supply-sanitation-technology-and-quality-standards`.
