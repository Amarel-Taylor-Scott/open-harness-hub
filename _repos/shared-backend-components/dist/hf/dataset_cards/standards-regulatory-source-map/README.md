---
license: CC-BY-4.0
tags:
- ai
- controls
- cross_industry
- experimental
- extraction
- finance
- governance
- government
- healthcare.public_health
- legal
- open-harness-hub
- public-facts
- regulations
- retrieval
- software.devops
- source-surfaces
- standards
- verification
- versioned-facts
task_categories:
- text-classification
- text-retrieval
- token-classification
size_categories:
- n<1K
language:
- en
pretty_name: Standards and regulatory source map
---

# Standards and regulatory source map

<!-- Generated from OpenHubForAI manifest `knowledge-pack/standards-regulatory-source-map` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

High-value standards, regulatory, public enforcement, disclosure, and public-health source surfaces for generating versioned facts, procedure objects, controls, evidence requirements, and RAG records.

**Industries**: ai, government, legal, healthcare.public_health, finance, software.devops, cross_industry
**Capabilities**: retrieval, verification, governance, extraction
**Modalities**: text, structured
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `source_surface`
- `source_family`
- `extraction_target`
- `governance_policy`

## Files

| path | format | schema |
|---|---|---|
| `data/standards-regulatory-source-map/surfaces.jsonl` | jsonl | — |

## Provenance

- **sources**: Official public source documentation and OpenHubForAI source-surface planning
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: source map only; no source records copied

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/standards-regulatory-source-map.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{standards-regulatory-source-map_open_harness_hub,
  title  = {Standards and regulatory source map},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/standards-regulatory-source-map},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/standards-regulatory-source-map`.
