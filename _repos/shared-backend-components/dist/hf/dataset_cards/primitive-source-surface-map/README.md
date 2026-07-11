---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- experimental
- governance
- million-primitives
- open-harness-hub
- planning
- primitive-database
- retrieval
- source-surfaces
- verified-sources
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Primitive source surface map
---

# Primitive source surface map

<!-- Generated from OpenHubForAI manifest `knowledge-pack/primitive-source-surface-map` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Initial routine scan surfaces for building a large indexed primitive database with keyword, vector, graph, and model-polished search.

**Industries**: ai, cross_industry
**Capabilities**: retrieval, planning, governance
**Modalities**: text, structured
**Freshness**: stable
**Trust boundary**: hub

## Content types (leaf vocabulary)

- `source_surface`
- `scan_policy`
- `publisher_lane`

## Files

| path | format | schema |
|---|---|---|
| `data/primitive-source-surface-map/surfaces.jsonl` | jsonl | — |

## Provenance

- **sources**: Data.gov Catalog API, OpenAlex API, Semantic Scholar API, NIST NVD API, openFDA, Public hiring and task marketplace metadata patterns
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: source metadata and synthetic task archetypes only; no worker/client PII, private messages, or proprietary listing text

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/primitive-source-surface-map.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{primitive-source-surface-map_open_harness_hub,
  title  = {Primitive source surface map},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/primitive-source-surface-map},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/primitive-source-surface-map`.
