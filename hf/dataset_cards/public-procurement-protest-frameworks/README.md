---
license: CC-BY-4.0
tags:
- expansion-v6
- experimental
- government.regulatory
- open-harness-hub
- procurement.sourcing
- public-procurement-protest
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Public Procurement Protest frameworks
---

# Public Procurement Protest frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/public-procurement-protest-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for public procurement protest workflows.

**Industries**: government.regulatory, procurement.sourcing
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
| `data/public-procurement-protest/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Public Procurement Protest control checklist, Public Procurement Protest evidence matrix, Public Procurement Protest escalation playbook, Public Procurement Protest benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-procurement-protest-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-procurement-protest-frameworks_open_harness_hub,
  title  = {Public Procurement Protest frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-procurement-protest-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-procurement-protest-frameworks`.
