---
license: CC-BY-4.0
tags:
- acs
- api-reference
- census
- cross_industry
- experimental
- facts
- government
- grounding
- open-harness-hub
- public-data
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: US Census API reference (ACS variables + geography hierarchy)
---

# US Census API reference (ACS variables + geography hierarchy)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/us-census-api-reference` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Grounding facts a bare LLM does not hold reliably: the exact American
Community Survey (ACS) variable codes (e.g. B19013_001E = median household
income, B01003_001E = total population) and the Census geography hierarchy +
`for`/`in` clause syntax used by the Census Data API.

Capability lift: models hallucinate variable codes and current figures.
Pairing this reference with `tool/us-census-acs-api` lets a pipeline fetch the
authoritative, current value and cite it, instead of guessing.

Geography hierarchy (coarse → fine): us → region → division → state → county →
county subdivision → tract → block group → block; plus place, ZCTA,
congressional district, and metropolitan/micropolitan statistical area (CBSA).

**Industries**: government, cross_industry
**Capabilities**: retrieval, verification
**Modalities**: structured, tabular
**Freshness**: stable
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/census-pack/acs-key-variables.jsonl` | jsonl | — |

## Provenance

- **source_url**: https://api.census.gov/data.html
- **publisher**: U.S. Census Bureau
- **license**: public-domain
- **freshness**: stable

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/us-census-api-reference.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{us-census-api-reference_open_harness_hub,
  title  = {US Census API reference (ACS variables + geography hierarchy)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/us-census-api-reference},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/us-census-api-reference`.
