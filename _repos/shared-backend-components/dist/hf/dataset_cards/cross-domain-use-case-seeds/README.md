---
license: CC-BY-4.0
tags:
- banking
- competition-analysis
- creative
- cross_industry
- experimental
- finance
- generation
- geographic-analysis
- governance
- government
- laws
- legal
- media
- moderation
- open-harness-hub
- planning
- retrieval
- use-case-seeds
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cross-domain use case seeds
---

# Cross-domain use case seeds

<!-- Generated from OpenHubForAI manifest `knowledge-pack/cross-domain-use-case-seeds` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Synthetic seed surfaces for banking laws, content moderation, content and creative creation, brainstorming, competition analysis, geographic analysis, and jurisdiction-specific law pipelines.

**Industries**: finance, legal, media, creative, government, cross_industry
**Capabilities**: planning, retrieval, generation, verification, governance
**Modalities**: text, image, structured
**Freshness**: volatile
**Trust boundary**: mixed

## Content types (leaf vocabulary)

- `use_case_seed`
- `pipeline_surface`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/cross-domain-use-case-seeds/seeds.jsonl` | jsonl | cross-domain-use-case-seed |

## Provenance

- **sources**: OpenHubForAI ideation notes
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: Synthetic seed descriptions only; excludes insurance-related pipeline seeds.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cross-domain-use-case-seeds.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cross-domain-use-case-seeds_open_harness_hub,
  title  = {Cross-domain use case seeds},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cross-domain-use-case-seeds},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cross-domain-use-case-seeds`.
