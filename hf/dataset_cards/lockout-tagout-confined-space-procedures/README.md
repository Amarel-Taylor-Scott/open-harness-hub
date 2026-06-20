---
license: CC-BY-4.0
tags:
- capability-lift
- construction
- esoteric
- experimental
- infrastructure
- ingestion-target
- knowledge-pack
- open-harness-hub
- rag_vector
- retrieval
- supply_chain
- trade
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Lockout Tagout Confined Space Procedures
---

# Lockout Tagout Confined Space Procedures

<!-- Generated from Open Harness Hub manifest `knowledge-pack/lockout-tagout-confined-space-procedures` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: blur OSHA 1910.147 LOTO vs 1910.146 confined-space; drop verification/test-order steps Grounded in OSHA 29 CFR 1910.147 & .146 + eTools (public domain) via rag_vector retrieval. Lift: ordered life-safety steps where invented/reordered step is dangerous

**Industries**: trade, supply_chain, construction, infrastructure
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
| `data/esoteric-packs/lockout-tagout-confined-space-procedures.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: OSHA 29 CFR 1910.147 & .146 + eTools (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/lockout-tagout-confined-space-procedures.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{lockout-tagout-confined-space-procedures_open_harness_hub,
  title  = {Lockout Tagout Confined Space Procedures},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/lockout-tagout-confined-space-procedures},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/lockout-tagout-confined-space-procedures`.
