---
license: CC-BY-4.0
tags:
- ai
- blueprints
- cost-estimation
- cross_industry
- deployment-options
- evaluation
- experimental
- finance
- governance
- government
- humanitarian
- model-routing
- open-harness-hub
- planning
- prefix-caching
- routing
- software.devops
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Costed blueprint route patterns
---

# Costed blueprint route patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/costed-blueprint-route-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Seed route-matrix patterns for turning user requests into cheap, balanced, quality-first, and local-first LLM pipeline deployment options.

**Industries**: ai, software.devops, government, finance, humanitarian, cross_industry
**Capabilities**: planning, routing, evaluation, governance
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `blueprint_route_pattern`
- `cost_matrix_pattern`
- `prompt_prefix_cache_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/costed-blueprint-route-patterns/patterns.jsonl` | jsonl | costed-blueprint-route-pattern |

## Provenance

- **sources**: User-provided Open Harness Hub SaaS and sentence-to-pipeline product direction from 2026-05-25, Open Harness Hub low-cost hosting and model-routing architecture docs
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic route examples only; no personal data or private customer content.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/costed-blueprint-route-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{costed-blueprint-route-patterns_open_harness_hub,
  title  = {Costed blueprint route patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/costed-blueprint-route-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/costed-blueprint-route-patterns`.
