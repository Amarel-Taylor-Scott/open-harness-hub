---
license: CC-BY-4.0
tags:
- agriculture
- aquaculture-health-monitoring
- environmental.water
- expansion-v6
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
pretty_name: Aquaculture Health Monitoring frameworks
---

# Aquaculture Health Monitoring frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/aquaculture-health-monitoring-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for aquaculture health monitoring workflows.

**Industries**: agriculture, environmental.water
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
| `data/aquaculture-health-monitoring/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Aquaculture Health Monitoring control checklist, Aquaculture Health Monitoring evidence matrix, Aquaculture Health Monitoring escalation playbook, Aquaculture Health Monitoring benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/aquaculture-health-monitoring-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{aquaculture-health-monitoring-frameworks_open_harness_hub,
  title  = {Aquaculture Health Monitoring frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/aquaculture-health-monitoring-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/aquaculture-health-monitoring-frameworks`.
