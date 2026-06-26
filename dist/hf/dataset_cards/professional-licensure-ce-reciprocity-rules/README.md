---
license: CC-BY-4.0
tags:
- capability-lift
- education
- esoteric
- experimental
- graph
- ingestion-target
- knowledge-pack
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
pretty_name: Professional Licensure Ce Reciprocity Rules
---

# Professional Licensure Ce Reciprocity Rules

<!-- Generated from OpenHubForAI manifest `knowledge-pack/professional-licensure-ce-reciprocity-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invent CE hours, renewal cycles, reciprocity/compact status per state/board Grounded in state board statutes + interstate compact commission docs (public) via graph retrieval. Lift: (profession x state x compact) join varying widely, updates often

**Industries**: education
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
| `data/esoteric-packs/professional-licensure-ce-reciprocity-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: state board statutes + interstate compact commission docs (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/professional-licensure-ce-reciprocity-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{professional-licensure-ce-reciprocity-rules_open_harness_hub,
  title  = {Professional Licensure Ce Reciprocity Rules},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/professional-licensure-ce-reciprocity-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/professional-licensure-ce-reciprocity-rules`.
