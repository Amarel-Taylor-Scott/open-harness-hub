---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- evaluation
- experimental
- extraction
- governance
- human-in-the-loop
- million-primitives
- open-harness-hub
- planning
- routing
- software.devops
- source-governance
- task-marketplace
- workflows
task_categories:
- text-classification
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Task marketplace archetype patterns
---

# Task marketplace archetype patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/task-marketplace-archetype-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Synthetic task-marketplace metadata patterns for deriving reusable workflow primitives, skill bundles, acceptance criteria, and human-in-loop review gates without storing raw listings or personal data.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: extraction, planning, governance, evaluation, routing
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `task_marketplace_source_record`
- `task_archetype_pattern`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl` | jsonl | schemas/source-record.schema.json |
| `catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl` | jsonl | schemas/normalized-object-record.schema.json |

## Provenance

- **sources**: Synthetic marketplace task archetypes based on common public task categories, Open Harness Hub primitive source surface map
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Synthetic metadata only; no raw marketplace listings, worker/client PII, private messages, or proprietary job-posting dumps.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/task-marketplace-archetype-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{task-marketplace-archetype-patterns_open_harness_hub,
  title  = {Task marketplace archetype patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/task-marketplace-archetype-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/task-marketplace-archetype-patterns`.
