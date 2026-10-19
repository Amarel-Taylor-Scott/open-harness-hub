---
license: CC-BY-4.0
tags:
- energy.grid
- environmental.water
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- utility-vegetation-management
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Utility Vegetation Management frameworks
---

# Utility Vegetation Management frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/utility-vegetation-management-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for utility vegetation management workflows.

**Industries**: energy.grid, environmental.water
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
| `data/utility-vegetation-management/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Utility Vegetation Management control checklist, Utility Vegetation Management evidence matrix, Utility Vegetation Management escalation playbook, Utility Vegetation Management benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/utility-vegetation-management-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{utility-vegetation-management-frameworks_open_harness_hub,
  title  = {Utility Vegetation Management frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/utility-vegetation-management-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/utility-vegetation-management-frameworks`.
