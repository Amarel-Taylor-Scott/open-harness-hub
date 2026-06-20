---
license: CC-BY-4.0
tags:
- ai
- blueprint-records
- cross_industry
- evaluation
- experimental
- finance
- governance
- government
- humanitarian
- indexing
- local-demo
- model-routing
- open-harness-hub
- planning
- pricing
- retrieval
- routing
- software.devops
- verified-facts
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Local blueprint output record patterns
---

# Local blueprint output record patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/local-blueprint-output-record-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Seed patterns for converting local sentence-to-pipeline demo outputs into normalized model-route, prompt-cache, pricing, eval, deployment, and verified-fact dependency records.

**Industries**: ai, software.devops, government, finance, humanitarian, cross_industry
**Capabilities**: planning, routing, evaluation, governance, retrieval
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `blueprint_output_record_pattern`
- `model_route_record_pattern`
- `prompt_prefix_cache_profile_pattern`
- `verified_fact_dependency_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/local-blueprint-output-record-patterns/patterns.jsonl` | jsonl | local-blueprint-output-record-pattern |

## Provenance

- **sources**: User-provided Open Harness Hub local sentence-to-pipeline product direction from 2026-05-25, Open Harness Hub costed blueprint route matrix architecture
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic output-record patterns only; no private prompts, PII, or customer data.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/local-blueprint-output-record-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{local-blueprint-output-record-patterns_open_harness_hub,
  title  = {Local blueprint output record patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/local-blueprint-output-record-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/local-blueprint-output-record-patterns`.
