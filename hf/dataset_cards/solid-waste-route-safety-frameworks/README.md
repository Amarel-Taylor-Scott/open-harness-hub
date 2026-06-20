---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- solid-waste-route-safety
- transportation.trucking
- verification
- waste.generator
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Solid Waste Route Safety frameworks
---

# Solid Waste Route Safety frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/solid-waste-route-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for solid waste route safety workflows.

**Industries**: waste.generator, transportation.trucking
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
| `data/solid-waste-route-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Solid Waste Route Safety control checklist, Solid Waste Route Safety evidence matrix, Solid Waste Route Safety escalation playbook, Solid Waste Route Safety benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/solid-waste-route-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{solid-waste-route-safety-frameworks_open_harness_hub,
  title  = {Solid Waste Route Safety frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/solid-waste-route-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/solid-waste-route-safety-frameworks`.
