---
license: CC-BY-4.0
tags:
- bridge-inspection-review
- expansion-v4
- experimental
- government.regulatory
- infrastructure.bridge
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
pretty_name: Bridge Inspection Review frameworks
---

# Bridge Inspection Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/bridge-inspection-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for bridge inspection review review, evidence, escalation, and benchmarking.

**Industries**: infrastructure.bridge, government.regulatory
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
| `data/bridge-inspection-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Bridge Inspection Review control checklist, Bridge Inspection Review evidence matrix, Bridge Inspection Review escalation playbook, Bridge Inspection Review benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/bridge-inspection-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{bridge-inspection-review-frameworks_open_harness_hub,
  title  = {Bridge Inspection Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/bridge-inspection-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/bridge-inspection-review-frameworks`.
