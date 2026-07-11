---
license: CC-BY-4.0
tags:
- compliance
- expansion-v5
- experimental
- open-harness-hub
- retail-product-compliance
- retail.merchandising
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Retail Product Compliance frameworks
---

# Retail Product Compliance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/retail-product-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for retail product compliance workflows.

**Industries**: retail.merchandising, compliance
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
| `data/retail-product-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Retail Product Compliance control checklist, Retail Product Compliance evidence matrix, Retail Product Compliance escalation playbook, Retail Product Compliance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/retail-product-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{retail-product-compliance-frameworks_open_harness_hub,
  title  = {Retail Product Compliance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/retail-product-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/retail-product-compliance-frameworks`.
