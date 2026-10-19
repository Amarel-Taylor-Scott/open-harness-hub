---
license: CC-BY-4.0
tags:
- expansion-v4
- experimental
- government.benefits
- humanitarian-disaster-needs
- humanitarian.disaster
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
pretty_name: Humanitarian Disaster Needs frameworks
---

# Humanitarian Disaster Needs frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/humanitarian-disaster-needs-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for humanitarian disaster needs review, evidence, escalation, and benchmarking.

**Industries**: humanitarian.disaster, government.benefits
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
| `data/humanitarian-disaster-needs/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Humanitarian Disaster Needs control checklist, Humanitarian Disaster Needs evidence matrix, Humanitarian Disaster Needs escalation playbook, Humanitarian Disaster Needs benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/humanitarian-disaster-needs-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{humanitarian-disaster-needs-frameworks_open_harness_hub,
  title  = {Humanitarian Disaster Needs frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/humanitarian-disaster-needs-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/humanitarian-disaster-needs-frameworks`.
