---
license: CC-BY-4.0
tags:
- experimental
- facilities-maintenance-workorders
- facilities.maintenance
- infrastructure
- open-harness-hub
- retrieval
- use-case-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Facilities Maintenance Workorders frameworks
---

# Facilities Maintenance Workorders frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/facilities-maintenance-workorders-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for facilities maintenance workorders use cases.

**Industries**: facilities.maintenance, infrastructure
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/facilities-maintenance-workorders/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: work order priority triage, preventive maintenance compliance, vendor completion evidence, life-safety system maintenance controls
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/facilities-maintenance-workorders-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{facilities-maintenance-workorders-frameworks_open_harness_hub,
  title  = {Facilities Maintenance Workorders frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/facilities-maintenance-workorders-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/facilities-maintenance-workorders-frameworks`.
