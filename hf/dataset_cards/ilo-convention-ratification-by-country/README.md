---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- graph
- ingestion-target
- knowledge-pack
- legal
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
pretty_name: Ilo Convention Ratification By Country
---

# Ilo Convention Ratification By Country

<!-- Generated from Open Harness Hub manifest `knowledge-pack/ilo-convention-ratification-by-country` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models can't state which ILO conventions a given country has ratified, when, or with what reservations; they assume universal adoption Grounded in ILO NORMLEX ratification database (ILO, public) via graph retrieval. Lift: (country x convention) ratification graph the model lacks; exact, verifiable, and ignored by frontier R&D (low economic value)

**Industries**: legal, compliance
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
| `data/esoteric-packs/ilo-convention-ratification-by-country.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: ILO NORMLEX ratification database (ILO, public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ilo-convention-ratification-by-country.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ilo-convention-ratification-by-country_open_harness_hub,
  title  = {Ilo Convention Ratification By Country},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ilo-convention-ratification-by-country},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ilo-convention-ratification-by-country`.
