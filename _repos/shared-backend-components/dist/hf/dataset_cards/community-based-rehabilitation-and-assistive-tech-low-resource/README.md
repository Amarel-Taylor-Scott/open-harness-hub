---
license: CC-BY-4.0
tags:
- capability-lift
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
pretty_name: Community Based Rehabilitation And Assistive Tech Low Resource
---

# Community Based Rehabilitation And Assistive Tech Low Resource

<!-- Generated from OpenHubForAI manifest `knowledge-pack/community-based-rehabilitation-and-assistive-tech-low-resource` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: high-resource clinical pathways miss WHO CBR matrix, low-cost assistive products, CRPD inclusion Grounded in WHO CBR Guidelines + Priority Assistive Products List + CRPD (reusable) via rag_vector retrieval. Lift: under-served by health systems AND AI R&D; exclusion/preventable disability stakes

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
| `data/esoteric-packs/community-based-rehabilitation-and-assistive-tech-low-resource.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: WHO CBR Guidelines + Priority Assistive Products List + CRPD (reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/community-based-rehabilitation-and-assistive-tech-low-resource.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{community-based-rehabilitation-and-assistive-tech-low-resource_open_harness_hub,
  title  = {Community Based Rehabilitation And Assistive Tech Low Resource},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/community-based-rehabilitation-and-assistive-tech-low-resource},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/community-based-rehabilitation-and-assistive-tech-low-resource`.
