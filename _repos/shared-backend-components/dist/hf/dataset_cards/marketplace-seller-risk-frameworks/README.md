---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- marketplace-seller-risk
- open-harness-hub
- retail.search
- retrieval
- security.fraud
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Marketplace Seller Risk frameworks
---

# Marketplace Seller Risk frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/marketplace-seller-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for marketplace seller risk workflows.

**Industries**: retail.search, security.fraud
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
| `data/marketplace-seller-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Marketplace Seller Risk control checklist, Marketplace Seller Risk evidence matrix, Marketplace Seller Risk escalation playbook, Marketplace Seller Risk benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/marketplace-seller-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{marketplace-seller-risk-frameworks_open_harness_hub,
  title  = {Marketplace Seller Risk frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/marketplace-seller-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/marketplace-seller-risk-frameworks`.
