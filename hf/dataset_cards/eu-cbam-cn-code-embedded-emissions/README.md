---
license: CC-BY-4.0
tags:
- capability-lift
- esg
- esoteric
- exact_id
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
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
pretty_name: Eu Cbam Cn Code Embedded Emissions
---

# Eu Cbam Cn Code Embedded Emissions

<!-- Generated from Open Harness Hub manifest `knowledge-pack/eu-cbam-cn-code-embedded-emissions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: don't know in-scope CN codes, default embedded-emission values, 2026 timeline Grounded in EU CBAM Reg 2023/956 + default-values guidance (EUR-Lex) via exact_id retrieval. Lift: CN-code-keyed scope + published default factors + phased timeline

**Industries**: trade, supply_chain, esg
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
| `data/esoteric-packs/eu-cbam-cn-code-embedded-emissions.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: EU CBAM Reg 2023/956 + default-values guidance (EUR-Lex)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/eu-cbam-cn-code-embedded-emissions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{eu-cbam-cn-code-embedded-emissions_open_harness_hub,
  title  = {Eu Cbam Cn Code Embedded Emissions},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/eu-cbam-cn-code-embedded-emissions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/eu-cbam-cn-code-embedded-emissions`.
