---
license: CC-BY-4.0
tags:
- crypto-exchange-transaction-monitoring
- expansion-v3
- experimental
- finance.aml
- open-harness-hub
- retrieval
- tax.crypto
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Crypto Exchange Transaction Monitoring frameworks
---

# Crypto Exchange Transaction Monitoring frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/crypto-exchange-transaction-monitoring-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for crypto exchange transaction monitoring reviews, including evidence, escalation, and remediation controls.

**Industries**: finance.aml, tax.crypto
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`

## Files

| path | format | schema |
|---|---|---|
| `data/crypto-exchange-transaction-monitoring/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Crypto Exchange Transaction Monitoring control checklist, Crypto Exchange Transaction Monitoring evidence matrix, Crypto Exchange Transaction Monitoring escalation playbook, Crypto Exchange Transaction Monitoring remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/crypto-exchange-transaction-monitoring-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{crypto-exchange-transaction-monitoring-frameworks_open_harness_hub,
  title  = {Crypto Exchange Transaction Monitoring frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/crypto-exchange-transaction-monitoring-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/crypto-exchange-transaction-monitoring-frameworks`.
