---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- hospitality
- open-harness-hub
- retrieval
- transportation
- travel-disruption-care
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Travel Disruption Care frameworks
---

# Travel Disruption Care frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/travel-disruption-care-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for travel disruption care reviews, including evidence, escalation, and remediation controls.

**Industries**: hospitality, transportation
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
| `data/travel-disruption-care/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Travel Disruption Care control checklist, Travel Disruption Care evidence matrix, Travel Disruption Care escalation playbook, Travel Disruption Care remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/travel-disruption-care-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{travel-disruption-care-frameworks_open_harness_hub,
  title  = {Travel Disruption Care frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/travel-disruption-care-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/travel-disruption-care-frameworks`.
