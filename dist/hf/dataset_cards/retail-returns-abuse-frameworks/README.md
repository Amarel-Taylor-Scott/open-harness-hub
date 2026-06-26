---
license: CC-BY-4.0
tags:
- experimental
- open-harness-hub
- retail
- retail-returns-abuse
- retail.support
- retrieval
- security.fraud
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Retail Returns Abuse frameworks
---

# Retail Returns Abuse frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/retail-returns-abuse-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering return policy exception governance, chargeback evidence preservation, customer fairness review, abuse-pattern velocity checks.

**Industries**: retail, retail.support, security.fraud
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/retail-returns-abuse/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: return policy exception governance, chargeback evidence preservation, customer fairness review, abuse-pattern velocity checks
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/retail-returns-abuse-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{retail-returns-abuse-frameworks_open_harness_hub,
  title  = {Retail Returns Abuse frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/retail-returns-abuse-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/retail-returns-abuse-frameworks`.
