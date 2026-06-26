---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- healthcare.clinical
- healthcare.payer
- home-health-plan-review
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
pretty_name: Home Health Plan Review frameworks
---

# Home Health Plan Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/home-health-plan-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for home health plan review workflows.

**Industries**: healthcare.clinical, healthcare.payer
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
| `data/home-health-plan-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Home Health Plan Review control checklist, Home Health Plan Review evidence matrix, Home Health Plan Review escalation playbook, Home Health Plan Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/home-health-plan-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{home-health-plan-review-frameworks_open_harness_hub,
  title  = {Home Health Plan Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/home-health-plan-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/home-health-plan-review-frameworks`.
