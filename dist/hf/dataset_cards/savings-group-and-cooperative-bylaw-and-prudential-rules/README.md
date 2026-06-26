---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- finance
- graph
- ingestion-target
- knowledge-pack
- legal
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
pretty_name: Savings Group And Cooperative Bylaw And Prudential Rules
---

# Savings Group And Cooperative Bylaw And Prudential Rules

<!-- Generated from OpenHubForAI manifest `knowledge-pack/savings-group-and-cooperative-bylaw-and-prudential-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: generic banking advice misses VSLA/SACCO/ROSCA mechanics, bylaw/share/dividend, prudential regimes Grounded in national cooperative acts + ILO/ICA + central-bank SACCO regs (public) via graph retrieval. Lift: (country x entity x rule) under-digitized; member savings loss stakes

**Industries**: finance, compliance, legal
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
| `data/esoteric-packs/savings-group-and-cooperative-bylaw-and-prudential-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: national cooperative acts + ILO/ICA + central-bank SACCO regs (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/savings-group-and-cooperative-bylaw-and-prudential-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{savings-group-and-cooperative-bylaw-and-prudential-rules_open_harness_hub,
  title  = {Savings Group And Cooperative Bylaw And Prudential Rules},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/savings-group-and-cooperative-bylaw-and-prudential-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/savings-group-and-cooperative-bylaw-and-prudential-rules`.
