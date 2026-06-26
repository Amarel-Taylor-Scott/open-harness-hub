---
license: CC-BY-4.0
tags:
- capability-lift
- construction
- esoteric
- experimental
- graph
- infrastructure
- knowledge-pack
- open-harness-hub
- retrieval
- seeded
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: 811 One Call Utility Locate Rules
---

# 811 One Call Utility Locate Rules

<!-- Generated from OpenHubForAI manifest `knowledge-pack/811-one-call-utility-locate-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invent uniform 48h notice/colors; rules vary by state one-call statute Grounded in state 811 statutes + APWA Uniform Color Code + CGA Best Practices (public) via graph retrieval. Lift: per-state notice windows/tolerance zones + fixed color map; wrong = struck lines

**Industries**: construction, infrastructure
**Capabilities**: retrieval, verification
**Modalities**: structured, text
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/esoteric-packs/811-one-call-utility-locate-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: state 811 statutes + APWA Uniform Color Code + CGA Best Practices (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/811-one-call-utility-locate-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{811-one-call-utility-locate-rules_open_harness_hub,
  title  = {811 One Call Utility Locate Rules},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/811-one-call-utility-locate-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/811-one-call-utility-locate-rules`.
