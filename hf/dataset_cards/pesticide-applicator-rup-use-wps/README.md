---
license: CC-BY-4.0
tags:
- agriculture
- capability-lift
- esoteric
- experimental
- food
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
pretty_name: Pesticide Applicator Rup Use Wps
---

# Pesticide Applicator Rup Use Wps

<!-- Generated from Open Harness Hub manifest `knowledge-pack/pesticide-applicator-rup-use-wps` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: confuse RUP categories, WPS re-entry intervals/AEZ, label-mandated PPE Grounded in EPA FIFRA 40 CFR 170 (WPS) + 40 CFR 171 (public domain) via graph retrieval. Lift: label/category-specific REI/AEZ/PPE; 'label is the law' so generated values unsafe

**Industries**: agriculture, food
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
| `data/esoteric-packs/pesticide-applicator-rup-use-wps.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: EPA FIFRA 40 CFR 170 (WPS) + 40 CFR 171 (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/pesticide-applicator-rup-use-wps.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{pesticide-applicator-rup-use-wps_open_harness_hub,
  title  = {Pesticide Applicator Rup Use Wps},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/pesticide-applicator-rup-use-wps},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/pesticide-applicator-rup-use-wps`.
