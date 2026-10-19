---
license: CC-BY-4.0
tags:
- clinical-coding-audit
- expansion-v6
- experimental
- healthcare.payer
- insurance.claims
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Clinical Coding Audit frameworks
---

# Clinical Coding Audit frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/clinical-coding-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for clinical coding audit workflows.

**Industries**: healthcare.payer, insurance.claims
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
| `data/clinical-coding-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Clinical Coding Audit control checklist, Clinical Coding Audit evidence matrix, Clinical Coding Audit escalation playbook, Clinical Coding Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/clinical-coding-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{clinical-coding-audit-frameworks_open_harness_hub,
  title  = {Clinical Coding Audit frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/clinical-coding-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/clinical-coding-audit-frameworks`.
