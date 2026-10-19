---
license: CC-BY-4.0
tags:
- employee-relations-investigation
- expansion-v5
- experimental
- hr.hiring
- hr.performance
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
pretty_name: Employee Relations Investigation frameworks
---

# Employee Relations Investigation frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/employee-relations-investigation-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for employee relations investigation workflows.

**Industries**: hr.performance, hr.hiring
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
| `data/employee-relations-investigation/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Employee Relations Investigation control checklist, Employee Relations Investigation evidence matrix, Employee Relations Investigation escalation playbook, Employee Relations Investigation benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/employee-relations-investigation-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{employee-relations-investigation-frameworks_open_harness_hub,
  title  = {Employee Relations Investigation frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/employee-relations-investigation-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/employee-relations-investigation-frameworks`.
