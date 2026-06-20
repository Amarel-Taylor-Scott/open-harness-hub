---
license: CC-BY-4.0
tags:
- energy.oil_gas
- expansion-v4
- experimental
- infrastructure
- oil-gas-pipeline-integrity
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
pretty_name: Oil Gas Pipeline Integrity frameworks
---

# Oil Gas Pipeline Integrity frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/oil-gas-pipeline-integrity-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for oil gas pipeline integrity review, evidence, escalation, and benchmarking.

**Industries**: energy.oil_gas, infrastructure
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
| `data/oil-gas-pipeline-integrity/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Oil Gas Pipeline Integrity control checklist, Oil Gas Pipeline Integrity evidence matrix, Oil Gas Pipeline Integrity escalation playbook, Oil Gas Pipeline Integrity benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/oil-gas-pipeline-integrity-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{oil-gas-pipeline-integrity-frameworks_open_harness_hub,
  title  = {Oil Gas Pipeline Integrity frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/oil-gas-pipeline-integrity-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/oil-gas-pipeline-integrity-frameworks`.
