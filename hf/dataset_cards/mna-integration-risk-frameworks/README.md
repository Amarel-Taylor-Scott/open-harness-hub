---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- m_and_a.due_diligence
- m_and_a.integration
- mna-integration-risk
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
pretty_name: M&A Integration Risk frameworks
---

# M&A Integration Risk frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/mna-integration-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for m&a integration risk review, evidence, escalation, and benchmarking.

**Industries**: m_and_a.integration, m_and_a.due_diligence
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
| `data/mna-integration-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: M&A Integration Risk control checklist, M&A Integration Risk evidence matrix, M&A Integration Risk escalation playbook, M&A Integration Risk benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/mna-integration-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{mna-integration-risk-frameworks_open_harness_hub,
  title  = {M&A Integration Risk frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/mna-integration-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/mna-integration-risk-frameworks`.
