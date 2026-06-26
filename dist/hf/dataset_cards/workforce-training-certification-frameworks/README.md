---
license: CC-BY-4.0
tags:
- education.workforce
- expansion-v7
- experimental
- hr.performance
- open-harness-hub
- retrieval
- verification
- workforce-training-certification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Workforce Training Certification frameworks
---

# Workforce Training Certification frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/workforce-training-certification-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for workforce training certification workflows.

**Industries**: education.workforce, hr.performance
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
| `data/workforce-training-certification/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Workforce Training Certification control checklist, Workforce Training Certification evidence matrix, Workforce Training Certification escalation playbook, Workforce Training Certification benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/workforce-training-certification-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{workforce-training-certification-frameworks_open_harness_hub,
  title  = {Workforce Training Certification frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/workforce-training-certification-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/workforce-training-certification-frameworks`.
