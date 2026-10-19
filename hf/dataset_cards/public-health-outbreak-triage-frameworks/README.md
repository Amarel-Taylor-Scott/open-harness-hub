---
license: CC-BY-4.0
tags:
- expansion-v3
- experimental
- government.regulatory
- healthcare.public_health
- open-harness-hub
- public-health-outbreak-triage
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Public Health Outbreak Triage frameworks
---

# Public Health Outbreak Triage frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/public-health-outbreak-triage-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for public health outbreak triage reviews, including evidence, escalation, and remediation controls.

**Industries**: healthcare.public_health, government.regulatory
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
| `data/public-health-outbreak-triage/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Public Health Outbreak Triage control checklist, Public Health Outbreak Triage evidence matrix, Public Health Outbreak Triage escalation playbook, Public Health Outbreak Triage remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-health-outbreak-triage-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-health-outbreak-triage-frameworks_open_harness_hub,
  title  = {Public Health Outbreak Triage frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-health-outbreak-triage-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-health-outbreak-triage-frameworks`.
