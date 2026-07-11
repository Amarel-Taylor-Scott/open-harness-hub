---
license: CC-BY-4.0
tags:
- drug-labeling-promo-review
- expansion-v4
- experimental
- marketing_ops.claims
- open-harness-hub
- pharma.pv
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Drug Labeling Promo Review frameworks
---

# Drug Labeling Promo Review frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/drug-labeling-promo-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for drug labeling promo review review, evidence, escalation, and benchmarking.

**Industries**: pharma.pv, marketing_ops.claims
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
| `data/drug-labeling-promo-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Drug Labeling Promo Review control checklist, Drug Labeling Promo Review evidence matrix, Drug Labeling Promo Review escalation playbook, Drug Labeling Promo Review benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/drug-labeling-promo-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{drug-labeling-promo-review-frameworks_open_harness_hub,
  title  = {Drug Labeling Promo Review frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/drug-labeling-promo-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/drug-labeling-promo-review-frameworks`.
