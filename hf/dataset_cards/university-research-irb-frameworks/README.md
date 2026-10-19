---
license: CC-BY-4.0
tags:
- education.higher
- expansion-v3
- experimental
- open-harness-hub
- retrieval
- scientific_research.social
- university-research-irb
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: University Research IRB frameworks
---

# University Research IRB frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/university-research-irb-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite context pack for university research irb reviews, including evidence, escalation, and remediation controls.

**Industries**: education.higher, scientific_research.social
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
| `data/university-research-irb/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: University Research IRB control checklist, University Research IRB evidence matrix, University Research IRB escalation playbook, University Research IRB remediation tracker
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/university-research-irb-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{university-research-irb-frameworks_open_harness_hub,
  title  = {University Research IRB frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/university-research-irb-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/university-research-irb-frameworks`.
