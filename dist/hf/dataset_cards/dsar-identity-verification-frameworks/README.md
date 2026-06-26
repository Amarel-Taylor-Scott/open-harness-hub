---
license: CC-BY-4.0
tags:
- dsar-identity-verification
- expansion-v5
- experimental
- open-harness-hub
- privacy.dsar
- retrieval
- security.fraud
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: DSAR Identity Verification frameworks
---

# DSAR Identity Verification frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/dsar-identity-verification-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for dsar identity verification workflows.

**Industries**: privacy.dsar, security.fraud
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
| `data/dsar-identity-verification/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: DSAR Identity Verification control checklist, DSAR Identity Verification evidence matrix, DSAR Identity Verification escalation playbook, DSAR Identity Verification benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dsar-identity-verification-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dsar-identity-verification-frameworks_open_harness_hub,
  title  = {DSAR Identity Verification frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dsar-identity-verification-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dsar-identity-verification-frameworks`.
