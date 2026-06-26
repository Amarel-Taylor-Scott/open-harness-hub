---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- healthcare
- ingestion-target
- knowledge-pack
- legal
- open-harness-hub
- pharma
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
pretty_name: Healthcare Fraud Abuse Stark Aks Fca
---

# Healthcare Fraud Abuse Stark Aks Fca

<!-- Generated from OpenHubForAI manifest `knowledge-pack/healthcare-fraud-abuse-stark-aks-fca` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: conflate Stark (strict-liability) vs Anti-Kickback (intent) vs FCA qui tam mechanics Grounded in Stark 42 USC 1395nn + AKS 42 USC 1320a-7b + OIG safe harbors + FCA (public domain) via rag_vector retrieval. Lift: distinct legal tests, exceptions/safe harbors, treble-damage stakes

**Industries**: healthcare, pharma, legal, compliance
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
| `data/esoteric-packs/healthcare-fraud-abuse-stark-aks-fca.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: Stark 42 USC 1395nn + AKS 42 USC 1320a-7b + OIG safe harbors + FCA (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/healthcare-fraud-abuse-stark-aks-fca.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{healthcare-fraud-abuse-stark-aks-fca_open_harness_hub,
  title  = {Healthcare Fraud Abuse Stark Aks Fca},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/healthcare-fraud-abuse-stark-aks-fca},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/healthcare-fraud-abuse-stark-aks-fca`.
