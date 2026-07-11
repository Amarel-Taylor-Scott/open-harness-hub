---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- finance
- graph
- knowledge-pack
- open-harness-hub
- retrieval
- seeded
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Ofac 50 Percent Rule Ownership Aggregation
---

# Ofac 50 Percent Rule Ownership Aggregation

<!-- Generated from OpenHubForAI manifest `knowledge-pack/ofac-50-percent-rule-ownership-aggregation` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: models treat 'not on SDN' as 'not sanctioned'; skip indirect/aggregated ownership math Grounded in OFAC 50% Rule guidance + SDN/Consolidated lists (public domain) via graph retrieval. Lift: requires ownership-graph traversal + percentage summation + live list

**Industries**: finance, compliance
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
| `data/esoteric-packs/ofac-50-percent-rule-ownership-aggregation.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: OFAC 50% Rule guidance + SDN/Consolidated lists (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ofac-50-percent-rule-ownership-aggregation.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ofac-50-percent-rule-ownership-aggregation_open_harness_hub,
  title  = {Ofac 50 Percent Rule Ownership Aggregation},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ofac-50-percent-rule-ownership-aggregation},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ofac-50-percent-rule-ownership-aggregation`.
