---
license: CC-BY-4.0
tags:
- cloud-cost-anomaly
- expansion-v3
- experimental
- open-harness-hub
- retrieval
- software.devops
- sre
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cloud Cost Anomaly frameworks
---

# Cloud Cost Anomaly frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/cloud-cost-anomaly-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for cloud cost anomaly reviews, including evidence, escalation, and remediation controls.

**Industries**: software.devops, sre
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
| `data/cloud-cost-anomaly/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Cloud Cost Anomaly control checklist, Cloud Cost Anomaly evidence matrix, Cloud Cost Anomaly escalation playbook, Cloud Cost Anomaly remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cloud-cost-anomaly-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cloud-cost-anomaly-frameworks_open_harness_hub,
  title  = {Cloud Cost Anomaly frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cloud-cost-anomaly-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cloud-cost-anomaly-frameworks`.
