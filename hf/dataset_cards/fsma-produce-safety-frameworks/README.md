---
license: CC-BY-4.0
tags:
- agriculture_compliance.fsma
- expansion-v7
- experimental
- food.safety
- fsma-produce-safety
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
pretty_name: FSMA Produce Safety frameworks
---

# FSMA Produce Safety frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/fsma-produce-safety-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for fsma produce safety workflows.

**Industries**: agriculture_compliance.fsma, food.safety
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
| `data/fsma-produce-safety/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: FSMA Produce Safety control checklist, FSMA Produce Safety evidence matrix, FSMA Produce Safety escalation playbook, FSMA Produce Safety benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fsma-produce-safety-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fsma-produce-safety-frameworks_open_harness_hub,
  title  = {FSMA Produce Safety frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fsma-produce-safety-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fsma-produce-safety-frameworks`.
