---
license: CC-BY-4.0
tags:
- building-code-inspection
- construction.permitting
- expansion-v3
- experimental
- infrastructure
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
pretty_name: Building Code Inspection frameworks
---

# Building Code Inspection frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/building-code-inspection-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for building code inspection reviews, including evidence, escalation, and remediation controls.

**Industries**: construction.permitting, infrastructure
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`

## Files

| path | format | schema |
|---|---|---|
| `data/building-code-inspection/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Building Code Inspection control checklist, Building Code Inspection evidence matrix, Building Code Inspection escalation playbook, Building Code Inspection remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/building-code-inspection-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{building-code-inspection-frameworks_open_harness_hub,
  title  = {Building Code Inspection frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/building-code-inspection-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/building-code-inspection-frameworks`.
