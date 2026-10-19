---
license: CC-BY-4.0
tags:
- education
- education-accommodations
- education.higher
- education.k12
- experimental
- open-harness-hub
- retrieval
- synthetic-expansion
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Education Accommodations frameworks
---

# Education Accommodations frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/education-accommodations-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite reference pack covering ADA reasonable accommodation process, Section 504 access obligations, FERPA privacy handling, implementation and faculty-notice workflow.

**Industries**: education, education.higher, education.k12
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `policy_summary`

## Files

| path | format | schema |
|---|---|---|
| `data/education-accommodations/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: ADA reasonable accommodation process, Section 504 access obligations, FERPA privacy handling, implementation and faculty-notice workflow
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/education-accommodations-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{education-accommodations-frameworks_open_harness_hub,
  title  = {Education Accommodations frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/education-accommodations-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/education-accommodations-frameworks`.
