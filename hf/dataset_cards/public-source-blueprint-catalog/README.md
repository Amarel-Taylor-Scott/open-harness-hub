---
license: CC-BY-4.0
tags:
- archive-capture
- automotive
- classification
- construction
- cross_industry
- energy
- esoteric-industries
- evaluation
- experimental
- extraction
- governance
- government
- manufacturing
- open-harness-hub
- public-sources
- retrieval
- scraping
- source-blueprints
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Public source blueprint catalog
---

# Public source blueprint catalog

<!-- Generated from Open Harness Hub manifest `knowledge-pack/public-source-blueprint-catalog` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Blueprint seeds for scanning public source families across automotive, employment agency, plumbing/HVAC, woodworking, offshore oil and gas, and environmental review verticals.

**Industries**: automotive, energy, manufacturing, construction, government, cross_industry
**Capabilities**: retrieval, extraction, classification, governance, evaluation
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `public_source_blueprint`
- `source_governance_plan`
- `scraper_normalizer_plan`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/public-source-blueprint-catalog/blueprints.jsonl` | jsonl | public-source-blueprint |

## Provenance

- **sources**: Open Harness Hub contributor-authored public source blueprint seeds, Open Harness Hub esoteric industry source surfaces
- **collected_through**: 2026-05-25
- **collected_by**: Open Harness Hub contributors
- **anonymization**: Blueprint metadata only; no scraped source bodies, real PII, proprietary manuals, or confidential records.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-source-blueprint-catalog.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-source-blueprint-catalog_open_harness_hub,
  title  = {Public source blueprint catalog},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-source-blueprint-catalog},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-source-blueprint-catalog`.
