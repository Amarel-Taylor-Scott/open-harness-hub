---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- government.permitting
- open-harness-hub
- real-estate-zoning-review
- real_estate.due_diligence
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Real Estate Zoning Review frameworks
---

# Real Estate Zoning Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/real-estate-zoning-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for real estate zoning review review, evidence, escalation, and benchmarking.

**Industries**: real_estate.due_diligence, government.permitting
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
| `data/real-estate-zoning-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Real Estate Zoning Review control checklist, Real Estate Zoning Review evidence matrix, Real Estate Zoning Review escalation playbook, Real Estate Zoning Review benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/real-estate-zoning-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{real-estate-zoning-review-frameworks_open_harness_hub,
  title  = {Real Estate Zoning Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/real-estate-zoning-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/real-estate-zoning-review-frameworks`.
