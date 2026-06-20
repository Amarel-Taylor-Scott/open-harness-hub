---
license: CC-BY-4.0
tags:
- agriculture_compliance.organic
- expansion-v6
- experimental
- open-harness-hub
- organic-certification-audit
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Organic Certification Audit frameworks
---

# Organic Certification Audit frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/organic-certification-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for organic certification audit workflows.

**Industries**: agriculture_compliance.organic
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
| `data/organic-certification-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Organic Certification Audit control checklist, Organic Certification Audit evidence matrix, Organic Certification Audit escalation playbook, Organic Certification Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/organic-certification-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{organic-certification-audit-frameworks_open_harness_hub,
  title  = {Organic Certification Audit frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/organic-certification-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/organic-certification-audit-frameworks`.
