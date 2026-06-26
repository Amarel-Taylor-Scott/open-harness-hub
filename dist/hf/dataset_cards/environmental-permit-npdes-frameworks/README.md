---
license: CC-BY-4.0
tags:
- compliance
- environmental-permit-npdes
- environmental.wastewater
- expansion-v3
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
pretty_name: Environmental Permit NPDES frameworks
---

# Environmental Permit NPDES frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/environmental-permit-npdes-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for environmental permit npdes reviews, including evidence, escalation, and remediation controls.

**Industries**: environmental.wastewater, compliance
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
| `data/environmental-permit-npdes/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Environmental Permit NPDES control checklist, Environmental Permit NPDES evidence matrix, Environmental Permit NPDES escalation playbook, Environmental Permit NPDES remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/environmental-permit-npdes-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{environmental-permit-npdes-frameworks_open_harness_hub,
  title  = {Environmental Permit NPDES frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/environmental-permit-npdes-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/environmental-permit-npdes-frameworks`.
