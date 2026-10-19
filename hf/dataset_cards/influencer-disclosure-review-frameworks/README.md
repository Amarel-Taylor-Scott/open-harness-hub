---
license: CC-BY-4.0
tags:
- expansion-v5
- experimental
- influencer-disclosure-review
- marketing_ops.claims
- media.distribution
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
pretty_name: Influencer Disclosure Review frameworks
---

# Influencer Disclosure Review frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/influencer-disclosure-review-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for influencer disclosure review workflows.

**Industries**: marketing_ops.claims, media.distribution
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
| `data/influencer-disclosure-review/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Influencer Disclosure Review control checklist, Influencer Disclosure Review evidence matrix, Influencer Disclosure Review escalation playbook, Influencer Disclosure Review benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/influencer-disclosure-review-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{influencer-disclosure-review-frameworks_open_harness_hub,
  title  = {Influencer Disclosure Review frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/influencer-disclosure-review-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/influencer-disclosure-review-frameworks`.
