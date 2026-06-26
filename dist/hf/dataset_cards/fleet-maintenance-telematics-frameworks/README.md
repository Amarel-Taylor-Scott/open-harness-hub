---
license: CC-BY-4.0
tags:
- automotive.fleet
- experimental
- fleet-maintenance-telematics
- open-harness-hub
- retrieval
- transportation
- use-case-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Fleet Maintenance Telematics frameworks
---

# Fleet Maintenance Telematics frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/fleet-maintenance-telematics-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for fleet maintenance telematics use cases.

**Industries**: automotive.fleet, transportation
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
| `data/fleet-maintenance-telematics/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: preventive maintenance compliance, telematics fault-code triage, driver vehicle inspection reports, fleet downtime root-cause review
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fleet-maintenance-telematics-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fleet-maintenance-telematics-frameworks_open_harness_hub,
  title  = {Fleet Maintenance Telematics frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fleet-maintenance-telematics-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fleet-maintenance-telematics-frameworks`.
