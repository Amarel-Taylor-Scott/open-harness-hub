---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- space-mission-anomaly
- space.launch
- space.orbital
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Space Mission Anomaly frameworks
---

# Space Mission Anomaly frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/space-mission-anomaly-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for space mission anomaly workflows.

**Industries**: space.orbital, space.launch
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
| `data/space-mission-anomaly/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Space Mission Anomaly control checklist, Space Mission Anomaly evidence matrix, Space Mission Anomaly escalation playbook, Space Mission Anomaly benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/space-mission-anomaly-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{space-mission-anomaly-frameworks_open_harness_hub,
  title  = {Space Mission Anomaly frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/space-mission-anomaly-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/space-mission-anomaly-frameworks`.
