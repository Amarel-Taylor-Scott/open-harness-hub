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
pretty_name: Curriculum Standards Alignment Graph
---

# Curriculum Standards Alignment Graph

<!-- Generated from OpenHubForAI manifest `knowledge-pack/curriculum-standards-alignment-graph` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: can't map a resource to correct curriculum tree node; cross-lingual retrieval against fixed taxonomy Grounded in LECR topics/content + Kolibri/Learning Equality taxonomies (CC-BY) via graph retrieval. Lift: winners built retrieve+rerank over topic graph w/ multilingual embeddings; standards-graph lifts F2

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
| `data/esoteric-packs/curriculum-standards-alignment-graph.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: LECR topics/content + Kolibri/Learning Equality taxonomies (CC-BY)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/curriculum-standards-alignment-graph.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{curriculum-standards-alignment-graph_open_harness_hub,
  title  = {Curriculum Standards Alignment Graph},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/curriculum-standards-alignment-graph},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/curriculum-standards-alignment-graph`.
