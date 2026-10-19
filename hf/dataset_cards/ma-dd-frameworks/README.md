---
license: CC-BY-4.0
tags:
- beta
- due-diligence
- finance
- legal
- m&a
- m_and_a
- m_and_a.due_diligence
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
pretty_name: M&A DD frameworks (legal / financial / IP / customer / HR / tax)
---

# M&A DD frameworks (legal / financial / IP / customer / HR / tax)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/ma-dd-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference: standard M&A DD checklist + R&W
insurance scope + IRC §382 NOL limits + WARN Act + standard
IP-assignment + open-source license compatibility matrix.

**Industries**: m_and_a, m_and_a.due_diligence, legal, finance
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/ma-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Composite of common M&A DD checklists + R&W insurance scope summaries
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts; check transaction-specific counsel.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ma-dd-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ma-dd-frameworks_open_harness_hub,
  title  = {M&A DD frameworks (legal / financial / IP / customer / HR / tax)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ma-dd-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ma-dd-frameworks`.
