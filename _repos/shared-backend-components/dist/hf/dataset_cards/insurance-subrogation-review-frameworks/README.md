---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- insurance-subrogation-review
- insurance.claims
- insurance.fraud
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
pretty_name: Insurance Subrogation Review frameworks
---

# Insurance Subrogation Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/insurance-subrogation-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for insurance subrogation review workflows.

**Industries**: insurance.claims, insurance.fraud
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
| `data/insurance-subrogation-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Insurance Subrogation Review control checklist, Insurance Subrogation Review evidence matrix, Insurance Subrogation Review escalation playbook, Insurance Subrogation Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/insurance-subrogation-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{insurance-subrogation-review-frameworks_open_harness_hub,
  title  = {Insurance Subrogation Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/insurance-subrogation-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/insurance-subrogation-review-frameworks`.
