---
license: CC-BY-4.0
tags:
- energy.grid
- expansion-v6
- experimental
- nuclear-work-order-risk
- nuclear.power
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
pretty_name: Nuclear Work Order Risk frameworks
---

# Nuclear Work Order Risk frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/nuclear-work-order-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for nuclear work order risk workflows.

**Industries**: nuclear.power, energy.grid
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
| `data/nuclear-work-order-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Nuclear Work Order Risk control checklist, Nuclear Work Order Risk evidence matrix, Nuclear Work Order Risk escalation playbook, Nuclear Work Order Risk benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/nuclear-work-order-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{nuclear-work-order-risk-frameworks_open_harness_hub,
  title  = {Nuclear Work Order Risk frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/nuclear-work-order-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/nuclear-work-order-risk-frameworks`.
