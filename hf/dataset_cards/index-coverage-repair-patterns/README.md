---
license: CC-BY-4.0
tags:
- ai
- components
- cross_industry
- daily-factory
- experimental
- governance
- hybrid-search
- index-coverage
- open-harness-hub
- pgvector
- planning
- repair
- retrieval
- software.devops
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Index coverage repair patterns
---

# Index coverage repair patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/index-coverage-repair-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for detecting and repairing missing keyword, vector, graph, facet, and quality index records in high-volume staged component batches.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: retrieval, governance, verification, planning
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `index_coverage_repair_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/index-coverage-repair-patterns/checks.jsonl` | jsonl | index_coverage_repair_check |

## Provenance

- **sources**: Open Harness Hub daily production rows, Open Harness Hub model-ops daily run, Open Harness Hub promotion readiness planner
- **collected_through**: 2026-05-26
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic operational checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/index-coverage-repair-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{index-coverage-repair-patterns_open_harness_hub,
  title  = {Index coverage repair patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/index-coverage-repair-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/index-coverage-repair-patterns`.
