---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
- graph
- ingestion-target
- knowledge-pack
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
pretty_name: Migrant Worker Recruitment Fee Rules
---

# Migrant Worker Recruitment Fee Rules

<!-- Generated from Open Harness Hub manifest `knowledge-pack/migrant-worker-recruitment-fee-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: LLMs don't know corridor-specific recruitment-fee bans, the employer-pays principle, or which intermediaries are licensed; they give generic answers that miss bilateral-agreement specifics Grounded in ILO General Principles & Operational Guidelines for Fair Recruitment + IRIS Standard + bilateral labor agreements (ILO, reusable) via graph retrieval. Lift: low economic_value + thin data + jurisdiction/corridor-specific = deep valley; high human stakes (debt bondage), exact rules verifiable against ILO texts

**Industries**: cross_industry
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
| `data/esoteric-packs/migrant-worker-recruitment-fee-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: ILO General Principles & Operational Guidelines for Fair Recruitment + IRIS Standard + bilateral labor agreements (ILO, reusable)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/migrant-worker-recruitment-fee-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{migrant-worker-recruitment-fee-rules_open_harness_hub,
  title  = {Migrant Worker Recruitment Fee Rules},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/migrant-worker-recruitment-fee-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/migrant-worker-recruitment-fee-rules`.
