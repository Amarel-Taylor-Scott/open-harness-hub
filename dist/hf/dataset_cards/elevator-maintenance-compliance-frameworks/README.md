---
license: CC-BY-4.0
tags:
- elevator-maintenance-compliance
- expansion-v4
- experimental
- facilities.maintenance
- infrastructure.elevator
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
pretty_name: Elevator Maintenance Compliance frameworks
---

# Elevator Maintenance Compliance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/elevator-maintenance-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for elevator maintenance compliance review, evidence, escalation, and benchmarking.

**Industries**: infrastructure.elevator, facilities.maintenance
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
| `data/elevator-maintenance-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Elevator Maintenance Compliance control checklist, Elevator Maintenance Compliance evidence matrix, Elevator Maintenance Compliance escalation playbook, Elevator Maintenance Compliance benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/elevator-maintenance-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{elevator-maintenance-compliance-frameworks_open_harness_hub,
  title  = {Elevator Maintenance Compliance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/elevator-maintenance-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/elevator-maintenance-compliance-frameworks`.
