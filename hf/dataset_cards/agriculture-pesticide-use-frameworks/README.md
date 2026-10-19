---
license: CC-BY-4.0
tags:
- agriculture-pesticide-use
- agriculture_compliance.gap
- agriculture_compliance.usda
- expansion-v6
- experimental
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
pretty_name: Agriculture Pesticide Use frameworks
---

# Agriculture Pesticide Use frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/agriculture-pesticide-use-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for agriculture pesticide use workflows.

**Industries**: agriculture_compliance.usda, agriculture_compliance.gap
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
| `data/agriculture-pesticide-use/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Agriculture Pesticide Use control checklist, Agriculture Pesticide Use evidence matrix, Agriculture Pesticide Use escalation playbook, Agriculture Pesticide Use benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/agriculture-pesticide-use-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{agriculture-pesticide-use-frameworks_open_harness_hub,
  title  = {Agriculture Pesticide Use frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/agriculture-pesticide-use-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/agriculture-pesticide-use-frameworks`.
