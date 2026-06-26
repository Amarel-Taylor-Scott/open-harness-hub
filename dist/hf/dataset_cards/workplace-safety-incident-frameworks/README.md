---
license: CC-BY-4.0
tags:
- ehs.audit
- experimental
- facilities
- facilities.workplace_safety
- open-harness-hub
- retrieval
- use-case-expansion
- verification
- workplace-safety-incident
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Workplace Safety Incident frameworks
---

# Workplace Safety Incident frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/workplace-safety-incident-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite operational reference pack for workplace safety incident use cases.

**Industries**: facilities, facilities.workplace_safety, ehs.audit
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
| `data/workplace-safety-incident/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: workplace incident investigation, hazard correction tracking, injury response documentation, near-miss and recurrence review
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/workplace-safety-incident-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{workplace-safety-incident-frameworks_open_harness_hub,
  title  = {Workplace Safety Incident frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/workplace-safety-incident-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/workplace-safety-incident-frameworks`.
