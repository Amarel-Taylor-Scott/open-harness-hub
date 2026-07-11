---
license: CC-BY-4.0
tags:
- alta
- astm
- beta
- esa
- open-harness-hub
- real-estate
- real_estate
- real_estate.due_diligence
- retrieval
- verification
- zoning
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Real estate DD standards (ALTA / ASTM ESA / Bldg Code / Zoning)
---

# Real estate DD standards (ALTA / ASTM ESA / Bldg Code / Zoning)

<!-- Generated from OpenHubForAI manifest `knowledge-pack/real-estate-dd-standards` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite educational reference: ALTA title insurance forms +
ASTM E1527-21 Phase I ESA standard + ASTM E1903-19 Phase II +
IBC structural code summary + common zoning code structures.

**Industries**: real_estate, real_estate.due_diligence
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/realestate-pack/standards.jsonl` | jsonl | — |

## Provenance

- **sources**: ALTA Title Insurance forms (composite), ASTM E1527-21 Phase I ESA (composite), ASTM E1903-19 Phase II ESA (composite), IBC + common zoning code structures (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/real-estate-dd-standards.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{real-estate-dd-standards_open_harness_hub,
  title  = {Real estate DD standards (ALTA / ASTM ESA / Bldg Code / Zoning)},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/real-estate-dd-standards},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/real-estate-dd-standards`.
