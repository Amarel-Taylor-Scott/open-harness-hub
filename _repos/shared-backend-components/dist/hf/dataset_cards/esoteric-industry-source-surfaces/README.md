---
license: CC-BY-4.0
tags:
- automotive
- classification
- construction
- cross_industry
- employment-agencies
- energy
- environmental-review
- evaluation
- experimental
- extraction
- governance
- government
- hvac
- manufacturing
- offshore-oil-gas
- open-harness-hub
- plumbing
- retrieval
- source-surfaces
- woodworking
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Esoteric industry source surfaces
---

# Esoteric industry source surfaces

<!-- Generated from OpenHubForAI manifest `knowledge-pack/esoteric-industry-source-surfaces` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Seed source surfaces for automotive sales and brokers, employment agencies, plumbing and HVAC systems, woodworking, offshore oil and gas, and environmental review primitives.

**Industries**: automotive, energy, manufacturing, construction, government, cross_industry
**Capabilities**: extraction, classification, retrieval, governance, evaluation
**Modalities**: text, image, structured
**Freshness**: stable
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `source_surface_seed`
- `candidate_primitive_seed`
- `capability_gap_surface`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/esoteric-industry-source-surfaces/seeds.jsonl` | jsonl | source-surface-seed |

## Provenance

- **sources**: OpenHubForAI contributor-authored synthetic source-surface seeds, User-provided vertical examples from the 1M object scaling goal
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: Synthetic source-surface metadata only; no real PII or proprietary manuals.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/esoteric-industry-source-surfaces.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{esoteric-industry-source-surfaces_open_harness_hub,
  title  = {Esoteric industry source surfaces},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/esoteric-industry-source-surfaces},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/esoteric-industry-source-surfaces`.
