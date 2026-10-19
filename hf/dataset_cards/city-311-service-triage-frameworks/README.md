---
license: CC-BY-4.0
tags:
- city-311-service-triage
- expansion-v6
- experimental
- facilities.maintenance
- government.benefits
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
pretty_name: City 311 Service Triage frameworks
---

# City 311 Service Triage frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/city-311-service-triage-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for city 311 service triage workflows.

**Industries**: government.benefits, facilities.maintenance
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
| `data/city-311-service-triage/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: City 311 Service Triage control checklist, City 311 Service Triage evidence matrix, City 311 Service Triage escalation playbook, City 311 Service Triage benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/city-311-service-triage-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{city-311-service-triage-frameworks_open_harness_hub,
  title  = {City 311 Service Triage frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/city-311-service-triage-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/city-311-service-triage-frameworks`.
