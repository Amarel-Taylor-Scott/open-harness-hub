---
license: CC-BY-4.0
tags:
- beta
- open-harness-hub
- retrieval
- space
- space.export_control
- space.launch
- space.orbital
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Space launch + range safety + ITAR/EAR frameworks
---

# Space launch + range safety + ITAR/EAR frameworks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/space-launch-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

14 CFR Part 450 + NASA-STD-8719.25 + RCC 319 + 22 CFR ITAR + 15 CFR EAR + 25-year LEO.

**Industries**: space, space.launch, space.export_control, space.orbital
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/space-pack/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: 14 CFR Part 450 (composite), NASA-STD-8719.25 (composite), RCC 319-19 (composite), 22 CFR 120-130 ITAR (composite), 15 CFR 730-774 EAR (composite)
- **collected_through**: 2026-04-30
- **note**: Composite educational extracts.

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/space-launch-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{space-launch-frameworks_open_harness_hub,
  title  = {Space launch + range safety + ITAR/EAR frameworks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/space-launch-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/space-launch-frameworks`.
