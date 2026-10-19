---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- government
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Landmine Erw Marking And Safe Behavior Procedures
---

# Landmine Erw Marking And Safe Behavior Procedures

<!-- Generated from Open Harness Hub manifest `knowledge-pack/landmine-erw-marking-and-safe-behavior-procedures` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: vague 'avoid area' advice; lacks IMAS marking conventions, survey categories, withdrawal drills Grounded in IMAS + GICHD + UNMAS country profiles (public) via rag_vector retrieval. Lift: niche humanitarian safety, no commercial signal; life-or-death for returnees

**Industries**: compliance, government
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
| `data/esoteric-packs/landmine-erw-marking-and-safe-behavior-procedures.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: IMAS + GICHD + UNMAS country profiles (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/landmine-erw-marking-and-safe-behavior-procedures.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{landmine-erw-marking-and-safe-behavior-procedures_open_harness_hub,
  title  = {Landmine Erw Marking And Safe Behavior Procedures},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/landmine-erw-marking-and-safe-behavior-procedures},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/landmine-erw-marking-and-safe-behavior-procedures`.
