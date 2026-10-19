---
license: CC-BY-4.0
tags:
- environmental.wastewater
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- verification
- wastewater-overflow-report
- water_utility.sdwa
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Wastewater Overflow Report frameworks
---

# Wastewater Overflow Report frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/wastewater-overflow-report-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for wastewater overflow report workflows.

**Industries**: environmental.wastewater, water_utility.sdwa
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
| `data/wastewater-overflow-report/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Wastewater Overflow Report control checklist, Wastewater Overflow Report evidence matrix, Wastewater Overflow Report escalation playbook, Wastewater Overflow Report benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/wastewater-overflow-report-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{wastewater-overflow-report-frameworks_open_harness_hub,
  title  = {Wastewater Overflow Report frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/wastewater-overflow-report-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/wastewater-overflow-report-frameworks`.
