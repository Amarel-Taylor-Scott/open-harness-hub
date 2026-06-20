---
license: CC-BY-4.0
tags:
- energy.grid
- expansion-v7
- experimental
- grid-outage-mutual-assist
- open-harness-hub
- retrieval
- sre.oncall
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Grid Outage Mutual Assist frameworks
---

# Grid Outage Mutual Assist frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/grid-outage-mutual-assist-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for grid outage mutual assist workflows.

**Industries**: energy.grid, sre.oncall
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
| `data/grid-outage-mutual-assist/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Grid Outage Mutual Assist control checklist, Grid Outage Mutual Assist evidence matrix, Grid Outage Mutual Assist escalation playbook, Grid Outage Mutual Assist benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/grid-outage-mutual-assist-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{grid-outage-mutual-assist-frameworks_open_harness_hub,
  title  = {Grid Outage Mutual Assist frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/grid-outage-mutual-assist-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/grid-outage-mutual-assist-frameworks`.
