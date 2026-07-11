---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- food-recall-effectiveness
- food.safety
- food_safety.recall
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
pretty_name: Food Recall Effectiveness frameworks
---

# Food Recall Effectiveness frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/food-recall-effectiveness-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for food recall effectiveness workflows.

**Industries**: food_safety.recall, food.safety
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`
- `benchmark_context`

## Files

| path | format | schema |
|---|---|---|
| `data/food-recall-effectiveness/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Food Recall Effectiveness control checklist, Food Recall Effectiveness evidence matrix, Food Recall Effectiveness escalation playbook, Food Recall Effectiveness benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/food-recall-effectiveness-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{food-recall-effectiveness-frameworks_open_harness_hub,
  title  = {Food Recall Effectiveness frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/food-recall-effectiveness-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/food-recall-effectiveness-frameworks`.
