---
license: CC-BY-4.0
tags:
- classification
- construction
- cross_industry
- energy
- evaluation
- excluded-scope-insurance
- experimental
- extraction
- finance
- governance
- government
- healthcare
- media
- million-objects
- object-factory
- open-harness-hub
- partitions
- retrieval
- routing
- scheduler
- software
- source-surfaces
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Source surface partition patterns
---

# Source surface partition patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/source-surface-partition-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Seed backlog of high-value source surfaces that should be split into resumable scan partitions before public-source discovery, snapshotting, normalization, entity linking, dedupe, indexing, and review.

**Industries**: government, software, media, construction, energy, finance, healthcare, cross_industry
**Capabilities**: retrieval, extraction, classification, governance, evaluation, routing
**Modalities**: text, structured, image
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `source_surface_partition_seed`
- `source_surface_priority_signal`
- `candidate_primitive_backlog`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/source-surface-partition-patterns/source-surfaces.jsonl` | jsonl | source_surface_partition_seed |

## Provenance

- **sources**: Open Harness Hub source-surface planning notes, Public source families listed in docs/codex/million-object-goal.md
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic seed metadata only; no raw source bodies or PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/source-surface-partition-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{source-surface-partition-patterns_open_harness_hub,
  title  = {Source surface partition patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/source-surface-partition-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/source-surface-partition-patterns`.
