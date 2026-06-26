---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- experimental
- ingestion-target
- knowledge-pack
- manufacturing
- open-harness-hub
- rag_vector
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Engineering Materials Property Datasheets
---

# Engineering Materials Property Datasheets

<!-- Generated from OpenHubForAI manifest `knowledge-pack/engineering-materials-property-datasheets` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invent grade-specific yield/modulus/density; conflate UNS vs AISI/SAE vs EN vs ASTM Grounded in NIST material DBs + public datasheets + ASM/UNS cross-refs via rag_vector retrieval. Lift: grade-specific safety-critical numeric constants not memorized accurately

**Industries**: manufacturing
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
| `data/esoteric-packs/engineering-materials-property-datasheets.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: NIST material DBs + public datasheets + ASM/UNS cross-refs
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/engineering-materials-property-datasheets.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{engineering-materials-property-datasheets_open_harness_hub,
  title  = {Engineering Materials Property Datasheets},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/engineering-materials-property-datasheets},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/engineering-materials-property-datasheets`.
