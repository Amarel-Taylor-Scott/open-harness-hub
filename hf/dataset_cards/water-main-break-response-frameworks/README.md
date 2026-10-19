---
license: CC-BY-4.0
tags:
- environmental.water
- expansion-v6
- experimental
- open-harness-hub
- retrieval
- verification
- water-main-break-response
- water_utility.sdwa
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Water Main Break Response frameworks
---

# Water Main Break Response frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/water-main-break-response-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for water main break response workflows.

**Industries**: water_utility.sdwa, environmental.water
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
| `data/water-main-break-response/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Water Main Break Response control checklist, Water Main Break Response evidence matrix, Water Main Break Response escalation playbook, Water Main Break Response benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/water-main-break-response-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{water-main-break-response-frameworks_open_harness_hub,
  title  = {Water Main Break Response frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/water-main-break-response-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/water-main-break-response-frameworks`.
