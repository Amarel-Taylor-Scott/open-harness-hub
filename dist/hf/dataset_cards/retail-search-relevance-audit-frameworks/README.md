---
license: CC-BY-4.0
tags:
- data_governance.quality
- expansion-v7
- experimental
- open-harness-hub
- retail-search-relevance-audit
- retail.search
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Retail Search Relevance Audit frameworks
---

# Retail Search Relevance Audit frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/retail-search-relevance-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for retail search relevance audit workflows.

**Industries**: retail.search, data_governance.quality
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
| `data/retail-search-relevance-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Retail Search Relevance Audit control checklist, Retail Search Relevance Audit evidence matrix, Retail Search Relevance Audit escalation playbook, Retail Search Relevance Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/retail-search-relevance-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{retail-search-relevance-audit-frameworks_open_harness_hub,
  title  = {Retail Search Relevance Audit frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/retail-search-relevance-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/retail-search-relevance-audit-frameworks`.
