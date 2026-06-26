---
license: CC-BY-4.0
tags:
- ai
- candidate-primitives
- cross_industry
- evaluation
- experimental
- governance
- million-primitives
- open-harness-hub
- planning
- promotion
- quality-gates
- review-routing
- routing
- software.devops
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Candidate primitive promotion patterns
---

# Candidate primitive promotion patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/candidate-primitive-promotion-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Scoring criteria and seed decisions for promoting high-volume candidate primitives into curated manifests, review queues, or retained JSONL candidates.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: evaluation, governance, planning, routing
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `promotion_decision`
- `promotion_scoring_policy`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/candidate-primitive-promotion-patterns/promotion-decisions.jsonl` | jsonl | schemas/promotion-decision.schema.json |

## Provenance

- **sources**: OpenHubForAI million object goal, OpenHubForAI quality gates, OpenHubForAI task marketplace archetype intake
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: Synthetic scoring examples only; no real PII, raw job postings, or proprietary listings.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/candidate-primitive-promotion-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{candidate-primitive-promotion-patterns_open_harness_hub,
  title  = {Candidate primitive promotion patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/candidate-primitive-promotion-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/candidate-primitive-promotion-patterns`.
