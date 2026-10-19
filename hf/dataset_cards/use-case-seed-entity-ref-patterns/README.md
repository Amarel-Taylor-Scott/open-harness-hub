---
license: CC-BY-4.0
tags:
- ai
- classification
- comparison-blocking
- creative
- cross_industry
- energy
- entity-resolution
- experimental
- extraction
- finance
- governance
- graph-search
- healthcare
- hybrid-search
- legal
- media
- open-harness-hub
- retrieval
- software.devops
- use-case-seeds
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Use case seed entity ref patterns
---

# Use case seed entity ref patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/use-case-seed-entity-ref-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Patterns for promoting flexible use-case seed labels, inputs, outputs, stages, and risk tiers into canonical entities and object_entity_ref graph rows.

**Industries**: ai, software.devops, finance, legal, media, creative, energy, healthcare, cross_industry
**Capabilities**: extraction, retrieval, classification, governance
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `canonical_entity_pattern`
- `object_entity_ref_pattern`
- `graph_index_edge_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/use-case-seed-entity-ref-patterns/rows.jsonl` | jsonl | use-case-seed-entity-ref-pattern |

## Provenance

- **sources**: Open Harness Hub use-case seed row exporter, Open Harness Hub source governance and entity resolution architecture
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic entity-linking patterns only; insurance scope is excluded.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/use-case-seed-entity-ref-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{use-case-seed-entity-ref-patterns_open_harness_hub,
  title  = {Use case seed entity ref patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/use-case-seed-entity-ref-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/use-case-seed-entity-ref-patterns`.
