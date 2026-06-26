---
license: CC-BY-4.0
tags:
- ai
- component-candidates
- coverage
- cross_industry
- daily-factory
- evaluation
- experimental
- gap-analysis
- governance
- open-harness-hub
- planning
- retrieval
- showcase-pipelines
- software.devops
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Showcase candidate coverage patterns
---

# Showcase candidate coverage patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/showcase-candidate-coverage-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Checks for comparing daily showcase pipeline templates with staged component candidates and routing missing or partial coverage into the next generation batch.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: planning, retrieval, evaluation, governance
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `showcase_candidate_coverage_check`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/showcase-candidate-coverage-patterns/checks.jsonl` | jsonl | showcase_candidate_coverage_check |

## Provenance

- **sources**: OpenHubForAI daily showcase pipeline factory, OpenHubForAI daily component candidate partitions, OpenHubForAI component template load planner
- **collected_through**: 2026-05-26
- **collected_by**: OpenHubForAI contributors
- **anonymization**: synthetic coverage checks only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/showcase-candidate-coverage-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{showcase-candidate-coverage-patterns_open_harness_hub,
  title  = {Showcase candidate coverage patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/showcase-candidate-coverage-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/showcase-candidate-coverage-patterns`.
