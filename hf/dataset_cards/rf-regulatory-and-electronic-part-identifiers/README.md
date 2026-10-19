---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- government
- ingestion-target
- knowledge-pack
- manufacturing
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
pretty_name: Rf Regulatory And Electronic Part Identifiers
---

# Rf Regulatory And Electronic Part Identifiers

<!-- Generated from Open Harness Hub manifest `knowledge-pack/rf-regulatory-and-electronic-part-identifiers` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: fabricate FCC IDs, band edges, duty-cycle limits, JEDEC packages, EIA markings Grounded in FCC OET DB + Part 15/ITU-R + ETSI EN 300 220 + JEDEC + EIA tables via exact_id retrieval. Lift: region-specific legally-binding band limits + assigned ids, exact

**Industries**: manufacturing, compliance, government
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
| `data/esoteric-packs/rf-regulatory-and-electronic-part-identifiers.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FCC OET DB + Part 15/ITU-R + ETSI EN 300 220 + JEDEC + EIA tables
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/rf-regulatory-and-electronic-part-identifiers.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{rf-regulatory-and-electronic-part-identifiers_open_harness_hub,
  title  = {Rf Regulatory And Electronic Part Identifiers},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/rf-regulatory-and-electronic-part-identifiers},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/rf-regulatory-and-electronic-part-identifiers`.
