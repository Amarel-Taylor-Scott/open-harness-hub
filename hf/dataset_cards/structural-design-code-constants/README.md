---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
- ingestion-target
- knowledge-pack
- manufacturing
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
pretty_name: Structural Design Code Constants
---

# Structural Design Code Constants

<!-- Generated from Open Harness Hub manifest `knowledge-pack/structural-design-code-constants` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misquote load/phi factors, load-combination equations across ASCE7/AISC360/ACI318/Eurocode Grounded in ASCE7/AISC360/ACI318 public load combos + Eurocode factor tables + AISC shapes via exact_id retrieval. Lift: edition-specific life-safety numeric coefficients, deterministically checkable

**Industries**: manufacturing
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
| `data/esoteric-packs/structural-design-code-constants.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: ASCE7/AISC360/ACI318 public load combos + Eurocode factor tables + AISC shapes
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/structural-design-code-constants.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{structural-design-code-constants_open_harness_hub,
  title  = {Structural Design Code Constants},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/structural-design-code-constants},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/structural-design-code-constants`.
