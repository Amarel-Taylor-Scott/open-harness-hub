---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- government
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
pretty_name: Artisanal Small Scale Mining Mercury Safety
---

# Artisanal Small Scale Mining Mercury Safety

<!-- Generated from OpenHubForAI manifest `knowledge-pack/artisanal-small-scale-mining-mercury-safety` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models lack ASM-specific mercury-handling, ventilation, and Minamata-Convention obligations for informal small-scale miners Grounded in Minamata Convention on Mercury + UNEP/ILO ASM guidance (public) via rag_vector retrieval. Lift: informal, low-income, under-regulated sector ignored by frontier R&D; safety rules exact and citeable

**Industries**: compliance, government
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
| `data/esoteric-packs/artisanal-small-scale-mining-mercury-safety.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Minamata Convention on Mercury + UNEP/ILO ASM guidance (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/artisanal-small-scale-mining-mercury-safety.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{artisanal-small-scale-mining-mercury-safety_open_harness_hub,
  title  = {Artisanal Small Scale Mining Mercury Safety},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/artisanal-small-scale-mining-mercury-safety},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/artisanal-small-scale-mining-mercury-safety`.
