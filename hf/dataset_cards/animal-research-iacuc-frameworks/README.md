---
license: CC-BY-4.0
tags:
- animal-research-iacuc
- expansion-v4
- experimental
- open-harness-hub
- research.animal_welfare
- retrieval
- scientific_research.bio
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Animal Research IACUC frameworks
---

# Animal Research IACUC frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/animal-research-iacuc-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Expanded composite context pack for animal research iacuc review, evidence, escalation, and benchmarking.

**Industries**: research.animal_welfare, scientific_research.bio
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
| `data/animal-research-iacuc/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Animal Research IACUC control checklist, Animal Research IACUC evidence matrix, Animal Research IACUC escalation playbook, Animal Research IACUC benchmark rubric context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/animal-research-iacuc-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{animal-research-iacuc-frameworks_open_harness_hub,
  title  = {Animal Research IACUC frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/animal-research-iacuc-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/animal-research-iacuc-frameworks`.
