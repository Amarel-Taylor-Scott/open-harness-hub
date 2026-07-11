---
license: CC-BY-4.0
tags:
- capability-lift
- cyber
- esoteric
- experimental
- infrastructure
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
pretty_name: Community Health Worker Protocols Low Resource
---

# Community Health Worker Protocols Low Resource

<!-- Generated from OpenHubForAI manifest `knowledge-pack/community-health-worker-protocols-low-resource` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models give resource-rich-context advice; they miss WHO IMCI/community protocols designed for settings without labs, imaging, or specialists Grounded in WHO IMCI + community health worker guidelines (WHO, reusable) via rag_vector retrieval. Lift: protocol-exact, low-resource-setting-specific, low commercial R&D attention = valley; high health stakes

**Industries**: infrastructure, cyber
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
| `data/esoteric-packs/community-health-worker-protocols-low-resource.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: WHO IMCI + community health worker guidelines (WHO, reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/community-health-worker-protocols-low-resource.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{community-health-worker-protocols-low-resource_open_harness_hub,
  title  = {Community Health Worker Protocols Low Resource},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/community-health-worker-protocols-low-resource},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/community-health-worker-protocols-low-resource`.
