---
license: MIT
tags:
- creative
- experimental
- open-harness-hub
- retrieval
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Lens physics primers
---

# Lens physics primers

<!-- Generated from Open Harness Hub manifest `knowledge-pack/lens-physics-primers` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Short physical-prior descriptors for camera lens behavior. Used by
image-gen prompt-shapers so prompts request physically plausible
combinations of focal length, aperture, distance, and field of view.

**Industries**: creative
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `physics_prior`

## Files

| path | format | schema |
|---|---|---|
| `data/lens-physics.jsonl` | jsonl | — |

## Provenance

- **sources**: Standard photographic optics references
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/lens-physics-primers.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{lens-physics-primers_open_harness_hub,
  title  = {Lens physics primers},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/lens-physics-primers},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `knowledge-pack/lens-physics-primers`.
