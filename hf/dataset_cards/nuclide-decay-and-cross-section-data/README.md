---
license: CC-BY-4.0
tags:
- capability-lift
- energy
- esoteric
- exact_id
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Nuclide Decay And Cross Section Data
---

# Nuclide Decay And Cross Section Data

<!-- Generated from Open Harness Hub manifest `knowledge-pack/nuclide-decay-and-cross-section-data` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: wrong half-lives, decay modes/branching, cross-sections; isotope confusion Grounded in IAEA Chart of Nuclides/ENSDF + NNDC (public) + ENDF via exact_id retrieval. Lift: per-nuclide physical constants exact, safety/dosimetry-critical

**Industries**: energy
**Capabilities**: retrieval, verification
**Modalities**: structured, text
**Freshness**: volatile
**Trust boundary**: external

## Content types (leaf vocabulary)

- `fact_table`
- `reference_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/esoteric-packs/nuclide-decay-and-cross-section-data.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: IAEA Chart of Nuclides/ENSDF + NNDC (public) + ENDF
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/nuclide-decay-and-cross-section-data.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{nuclide-decay-and-cross-section-data_open_harness_hub,
  title  = {Nuclide Decay And Cross Section Data},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/nuclide-decay-and-cross-section-data},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/nuclide-decay-and-cross-section-data`.
