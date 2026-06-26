---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
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
pretty_name: Unhcr Asylum Rsd Procedures By Country
---

# Unhcr Asylum Rsd Procedures By Country

<!-- Generated from OpenHubForAI manifest `knowledge-pack/unhcr-asylum-rsd-procedures-by-country` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: LLMs invent refugee status determination steps, appeal timelines, and documentary requirements that vary sharply by country of asylum Grounded in UNHCR RSD procedural standards + country operations guidance (UNHCR, reusable) via rag_vector retrieval. Lift: procedure-heavy, country-specific, low-resource population; no automated success signal so models lag — classic valley with high humanitarian stakes

**Industries**: cross_industry
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
| `data/esoteric-packs/unhcr-asylum-rsd-procedures-by-country.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: UNHCR RSD procedural standards + country operations guidance (UNHCR, reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/unhcr-asylum-rsd-procedures-by-country.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{unhcr-asylum-rsd-procedures-by-country_open_harness_hub,
  title  = {Unhcr Asylum Rsd Procedures By Country},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/unhcr-asylum-rsd-procedures-by-country},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/unhcr-asylum-rsd-procedures-by-country`.
