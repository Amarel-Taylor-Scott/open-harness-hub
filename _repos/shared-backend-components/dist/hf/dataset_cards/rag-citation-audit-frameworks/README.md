---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- expansion-v3
- experimental
- open-harness-hub
- rag-citation-audit
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: RAG Citation Audit frameworks
---

# RAG Citation Audit frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/rag-citation-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for rag citation audit reviews, including evidence, escalation, and remediation controls.

**Industries**: ai, cross_industry
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
| `data/rag-citation-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: RAG Citation Audit control checklist, RAG Citation Audit evidence matrix, RAG Citation Audit escalation playbook, RAG Citation Audit remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rag-citation-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rag-citation-audit-frameworks_open_harness_hub,
  title  = {RAG Citation Audit frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rag-citation-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rag-citation-audit-frameworks`.
