---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- legal-litigation-hold
- legal.litigation
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
pretty_name: Legal Litigation Hold frameworks
---

# Legal Litigation Hold frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/legal-litigation-hold-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for legal litigation hold reviews, including evidence, escalation, and remediation controls.

**Industries**: legal.litigation
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
| `data/legal-litigation-hold/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Legal Litigation Hold control checklist, Legal Litigation Hold evidence matrix, Legal Litigation Hold escalation playbook, Legal Litigation Hold remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/legal-litigation-hold-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{legal-litigation-hold-frameworks_open_harness_hub,
  title  = {Legal Litigation Hold frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/legal-litigation-hold-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/legal-litigation-hold-frameworks`.
