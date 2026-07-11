---
license: CC-BY-4.0
tags:
- ccpa-optout-audit
- expansion-v7
- experimental
- marketing_ops.consent
- open-harness-hub
- privacy.ccpa
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: CCPA Optout Audit frameworks
---

# CCPA Optout Audit frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/ccpa-optout-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for ccpa optout audit workflows.

**Industries**: privacy.ccpa, marketing_ops.consent
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
| `data/ccpa-optout-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: CCPA Optout Audit control checklist, CCPA Optout Audit evidence matrix, CCPA Optout Audit escalation playbook, CCPA Optout Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ccpa-optout-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ccpa-optout-audit-frameworks_open_harness_hub,
  title  = {CCPA Optout Audit frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ccpa-optout-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ccpa-optout-audit-frameworks`.
