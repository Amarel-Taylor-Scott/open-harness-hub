---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
- healthcare
- knowledge-pack
- open-harness-hub
- pharma
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
pretty_name: Dea Controlled Substance Scheduling And Limits
---

# Dea Controlled Substance Scheduling And Limits

<!-- Generated from OpenHubForAI manifest `knowledge-pack/dea-controlled-substance-scheduling-and-limits` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misstate DEA schedules, rescheduling, refill/partial-fill limits, EPCS rules Grounded in DEA CSA schedules 21 CFR 1308 + Diversion Control (public domain) via exact_id retrieval. Lift: per-substance exact regulatory facts changing via rulemaking; wrong = illegal dispense

**Industries**: healthcare, pharma
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
| `data/esoteric-packs/dea-controlled-substance-scheduling-and-limits.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: DEA CSA schedules 21 CFR 1308 + Diversion Control (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/dea-controlled-substance-scheduling-and-limits.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{dea-controlled-substance-scheduling-and-limits_open_harness_hub,
  title  = {Dea Controlled Substance Scheduling And Limits},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/dea-controlled-substance-scheduling-and-limits},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/dea-controlled-substance-scheduling-and-limits`.
