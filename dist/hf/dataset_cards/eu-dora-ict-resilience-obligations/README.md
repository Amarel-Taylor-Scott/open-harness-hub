---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- experimental
- finance
- ingestion-target
- knowledge-pack
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
pretty_name: Eu Dora Ict Resilience Obligations
---

# Eu Dora Ict Resilience Obligations

<!-- Generated from OpenHubForAI manifest `knowledge-pack/eu-dora-ict-resilience-obligations` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: confuse DORA incident-classification thresholds, register-of-information fields, TLPT scope Grounded in EU DORA Reg 2022/2554 + RTS/ITS (EUR-Lex) via rag_vector retrieval. Lift: new (Jan 2025) regime past training emphasis; prescriptive timelines

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
| `data/esoteric-packs/eu-dora-ict-resilience-obligations.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: EU DORA Reg 2022/2554 + RTS/ITS (EUR-Lex)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/eu-dora-ict-resilience-obligations.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{eu-dora-ict-resilience-obligations_open_harness_hub,
  title  = {Eu Dora Ict Resilience Obligations},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/eu-dora-ict-resilience-obligations},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/eu-dora-ict-resilience-obligations`.
