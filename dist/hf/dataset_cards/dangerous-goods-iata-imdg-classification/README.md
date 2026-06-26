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
- maritime
- open-harness-hub
- retrieval
- transportation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Dangerous Goods Iata Imdg Classification
---

# Dangerous Goods Iata Imdg Classification

<!-- Generated from OpenHubForAI manifest `knowledge-pack/dangerous-goods-iata-imdg-classification` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misassign UN numbers, packing groups, segregation, lithium-battery sections; air vs sea deltas Grounded in UN Model Regs + ICAO TI / IMDG public summaries via exact_id retrieval. Lift: exact coded lookup with mode-specific deltas; hallucinated codes safety-critical

**Industries**: transportation, maritime, compliance, government
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
| `data/esoteric-packs/dangerous-goods-iata-imdg-classification.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: UN Model Regs + ICAO TI / IMDG public summaries
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dangerous-goods-iata-imdg-classification.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dangerous-goods-iata-imdg-classification_open_harness_hub,
  title  = {Dangerous Goods Iata Imdg Classification},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dangerous-goods-iata-imdg-classification},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dangerous-goods-iata-imdg-classification`.
