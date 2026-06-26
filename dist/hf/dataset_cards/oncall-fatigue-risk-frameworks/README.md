---
license: CC-BY-4.0
tags:
- expansion-v7
- experimental
- hr.performance
- oncall-fatigue-risk
- open-harness-hub
- retrieval
- sre.oncall
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: On-call Fatigue Risk frameworks
---

# On-call Fatigue Risk frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/oncall-fatigue-risk-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for on-call fatigue risk workflows.

**Industries**: sre.oncall, hr.performance
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
| `data/oncall-fatigue-risk/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: On-call Fatigue Risk control checklist, On-call Fatigue Risk evidence matrix, On-call Fatigue Risk escalation playbook, On-call Fatigue Risk benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/oncall-fatigue-risk-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{oncall-fatigue-risk-frameworks_open_harness_hub,
  title  = {On-call Fatigue Risk frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/oncall-fatigue-risk-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/oncall-fatigue-risk-frameworks`.
