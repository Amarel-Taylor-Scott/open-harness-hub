---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- facilities.maintenance
- hvac-commissioning-review
- infrastructure.hvac
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
pretty_name: HVAC Commissioning Review frameworks
---

# HVAC Commissioning Review frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/hvac-commissioning-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for hvac commissioning review review, evidence, escalation, and benchmarking.

**Industries**: infrastructure.hvac, facilities.maintenance
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
| `data/hvac-commissioning-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: HVAC Commissioning Review control checklist, HVAC Commissioning Review evidence matrix, HVAC Commissioning Review escalation playbook, HVAC Commissioning Review benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hvac-commissioning-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hvac-commissioning-review-frameworks_open_harness_hub,
  title  = {HVAC Commissioning Review frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hvac-commissioning-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hvac-commissioning-review-frameworks`.
