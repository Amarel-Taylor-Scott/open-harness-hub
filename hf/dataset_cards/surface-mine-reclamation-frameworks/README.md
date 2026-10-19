---
license: CC-BY-4.0
tags:
- environmental.water
- expansion-v7
- experimental
- mining.surface
- open-harness-hub
- retrieval
- surface-mine-reclamation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Surface Mine Reclamation frameworks
---

# Surface Mine Reclamation frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/surface-mine-reclamation-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for surface mine reclamation workflows.

**Industries**: mining.surface, environmental.water
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
| `data/surface-mine-reclamation/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Surface Mine Reclamation control checklist, Surface Mine Reclamation evidence matrix, Surface Mine Reclamation escalation playbook, Surface Mine Reclamation benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/surface-mine-reclamation-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{surface-mine-reclamation-frameworks_open_harness_hub,
  title  = {Surface Mine Reclamation frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/surface-mine-reclamation-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/surface-mine-reclamation-frameworks`.
