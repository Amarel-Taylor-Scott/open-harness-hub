---
license: CC-BY-4.0
tags:
- environmental.water
- expansion-v6
- experimental
- forestry-harvest-compliance
- open-harness-hub
- retrieval
- sustainability
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Forestry Harvest Compliance frameworks
---

# Forestry Harvest Compliance frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/forestry-harvest-compliance-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for forestry harvest compliance workflows.

**Industries**: environmental.water, sustainability
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
| `data/forestry-harvest-compliance/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Forestry Harvest Compliance control checklist, Forestry Harvest Compliance evidence matrix, Forestry Harvest Compliance escalation playbook, Forestry Harvest Compliance benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: OpenHubForAI contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/forestry-harvest-compliance-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{forestry-harvest-compliance-frameworks_open_harness_hub,
  title  = {Forestry Harvest Compliance frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/forestry-harvest-compliance-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/forestry-harvest-compliance-frameworks`.
