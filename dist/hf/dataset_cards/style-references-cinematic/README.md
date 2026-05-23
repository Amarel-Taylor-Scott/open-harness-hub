---
license: CC-BY-4.0
tags:
- cinematic
- creative
- experimental
- image-gen
- open-harness-hub
- retrieval
- style-reference
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cinematic style references
---

# Cinematic style references

<!-- Generated from Open Harness Hub manifest `knowledge-pack/style-references-cinematic` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Curated style descriptors for cinematic product / scene photography.
Each entry is a textual descriptor of a style — lighting, color
palette, composition, atmosphere — with attribution to the public
reference it generalizes.

**Industries**: creative
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `style_reference`

## Files

| path | format | schema |
|---|---|---|
| `data/cinematic.jsonl` | jsonl | — |

## Provenance

- **sources**: Public domain photography references, Editorial photography books
- **collected_through**: 2026-04-30
- **anonymization**: n/a

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/style-references-cinematic.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{style-references-cinematic_open_harness_hub,
  title  = {Cinematic style references},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/style-references-cinematic},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub artifact: `knowledge-pack/style-references-cinematic`.
