---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- hr.performance
- open-harness-hub
- retail.support
- retrieval
- verification
- workforce-scheduling-compliance
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Workforce Scheduling Compliance frameworks
---

# Workforce Scheduling Compliance frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/workforce-scheduling-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for workforce scheduling compliance workflows.

**Industries**: hr.performance, retail.support
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
| `data/workforce-scheduling-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Workforce Scheduling Compliance control checklist, Workforce Scheduling Compliance evidence matrix, Workforce Scheduling Compliance escalation playbook, Workforce Scheduling Compliance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/workforce-scheduling-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{workforce-scheduling-compliance-frameworks_open_harness_hub,
  title  = {Workforce Scheduling Compliance frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/workforce-scheduling-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/workforce-scheduling-compliance-frameworks`.
