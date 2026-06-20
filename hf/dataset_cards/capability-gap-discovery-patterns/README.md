---
license: CC-BY-4.0
tags:
- ai
- browser-scout
- capability-gap
- cross_industry
- evaluation
- experimental
- open-harness-hub
- pipeline-discovery
- planning
- primitive-priority
- research
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Capability gap discovery patterns
---

# Capability gap discovery patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/capability-gap-discovery-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Stable heuristics for using browser/search agents to find high-value LLM capability gaps, primitive opportunities, and deployable pipeline ideas.

**Industries**: ai, cross_industry
**Capabilities**: research, planning, evaluation
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `discovery_pattern`
- `scoring_rule`
- `promotion_rule`

## Files

| path | format | schema |
|---|---|---|
| `data/capability-gap-discovery-patterns/patterns.jsonl` | jsonl | — |

## Provenance

- **sources**: Open Harness Hub capability gap discovery workflow, Kaggle datasets and competitions, arXiv API, Semantic Scholar API
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: synthetic planning patterns only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/capability-gap-discovery-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{capability-gap-discovery-patterns_open_harness_hub,
  title  = {Capability gap discovery patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/capability-gap-discovery-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/capability-gap-discovery-patterns`.
