---
license: CC0-1.0
tags:
- experimental
- finance
- finance.aml
- finance.kyc
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
pretty_name: Sanctions list (shape, with placeholder entries)
---

# Sanctions list (shape, with placeholder entries)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/sanctions-list-shape` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference SHAPE for sanctions list integration. Real data must be
pulled from OFAC, UN, EU, HMT, or the institution's licensed
provider; this pack illustrates the row schema, not the entries.
Each row is an entity (individual or organization) with
normalized name, source list, listing date, and aliases.

**Industries**: finance, finance.aml, finance.kyc
**Capabilities**: retrieval, verification
**Modalities**: structured
**Freshness**: volatile
**Trust boundary**: local

## Content types (leaf vocabulary)

- `entity_signal`

## Files

| path | format | schema |
|---|---|---|
| `data/sanctions-shape.jsonl` | jsonl | — |

## Provenance

- **sources**: Synthetic placeholder rows. Use OFAC SDN / UN / EU lists in production.
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/sanctions-list-shape.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{sanctions-list-shape_open_harness_hub,
  title  = {Sanctions list (shape, with placeholder entries)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/sanctions-list-shape},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/sanctions-list-shape`.
