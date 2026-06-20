---
license: CC-BY-4.0
tags:
- climate
- climate-transition-plan
- esg.csrd
- expansion-v7
- experimental
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
pretty_name: Climate Transition Plan frameworks
---

# Climate Transition Plan frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/climate-transition-plan-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for climate transition plan workflows.

**Industries**: climate, esg.csrd
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
| `data/climate-transition-plan/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Climate Transition Plan control checklist, Climate Transition Plan evidence matrix, Climate Transition Plan escalation playbook, Climate Transition Plan benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/climate-transition-plan-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{climate-transition-plan-frameworks_open_harness_hub,
  title  = {Climate Transition Plan frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/climate-transition-plan-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/climate-transition-plan-frameworks`.
