---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
- government
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
pretty_name: Va Disability Rating Schedule Combined
---

# Va Disability Rating Schedule Combined

<!-- Generated from Open Harness Hub manifest `knowledge-pack/va-disability-rating-schedule-combined` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: add ratings arithmetically (wrong); miss combined-ratings table + bilateral factor Grounded in VA 38 CFR Part 4 + combined-ratings table (public domain) via exact_id retrieval. Lift: deterministic table lookup the model gets wrong by naive addition

**Industries**: government
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
| `data/esoteric-packs/va-disability-rating-schedule-combined.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: VA 38 CFR Part 4 + combined-ratings table (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/va-disability-rating-schedule-combined.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{va-disability-rating-schedule-combined_open_harness_hub,
  title  = {Va Disability Rating Schedule Combined},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/va-disability-rating-schedule-combined},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/va-disability-rating-schedule-combined`.
