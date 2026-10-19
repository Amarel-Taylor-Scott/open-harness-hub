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
pretty_name: Epa 608 Refrigerant Handling Rules
---

# Epa 608 Refrigerant Handling Rules

<!-- Generated from Open Harness Hub manifest `knowledge-pack/epa-608-refrigerant-handling-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: conflate refrigerant classes, recovery vacuum levels, leak-rate triggers, 608 cert scope Grounded in EPA 40 CFR 82 Subpart F + Section 608 fact sheets (public domain) via rag_vector retrieval. Lift: exact numeric thresholds, version-dated; wrong = EPA violation

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
| `data/esoteric-packs/epa-608-refrigerant-handling-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: EPA 40 CFR 82 Subpart F + Section 608 fact sheets (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/epa-608-refrigerant-handling-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{epa-608-refrigerant-handling-rules_open_harness_hub,
  title  = {Epa 608 Refrigerant Handling Rules},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/epa-608-refrigerant-handling-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/epa-608-refrigerant-handling-rules`.
