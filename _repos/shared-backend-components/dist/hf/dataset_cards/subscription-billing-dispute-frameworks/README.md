---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- finance.fraud
- open-harness-hub
- retail.support
- retrieval
- subscription-billing-dispute
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Subscription Billing Dispute frameworks
---

# Subscription Billing Dispute frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/subscription-billing-dispute-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for subscription billing dispute workflows.

**Industries**: retail.support, finance.fraud
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
| `data/subscription-billing-dispute/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Subscription Billing Dispute control checklist, Subscription Billing Dispute evidence matrix, Subscription Billing Dispute escalation playbook, Subscription Billing Dispute benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/subscription-billing-dispute-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{subscription-billing-dispute-frameworks_open_harness_hub,
  title  = {Subscription Billing Dispute frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/subscription-billing-dispute-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/subscription-billing-dispute-frameworks`.
