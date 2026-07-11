---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- open-harness-hub
- rail-crew-hours-compliance
- retrieval
- transportation.rail
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Rail Crew Hours Compliance frameworks
---

# Rail Crew Hours Compliance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/rail-crew-hours-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for rail crew hours compliance workflows.

**Industries**: transportation.rail
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
| `data/rail-crew-hours-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Rail Crew Hours Compliance control checklist, Rail Crew Hours Compliance evidence matrix, Rail Crew Hours Compliance escalation playbook, Rail Crew Hours Compliance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rail-crew-hours-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rail-crew-hours-compliance-frameworks_open_harness_hub,
  title  = {Rail Crew Hours Compliance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rail-crew-hours-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rail-crew-hours-compliance-frameworks`.
