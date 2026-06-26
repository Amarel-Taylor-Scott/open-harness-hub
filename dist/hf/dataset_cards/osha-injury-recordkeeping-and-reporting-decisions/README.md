---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- compliance
- cyber
- esoteric
- experimental
- government
- ingestion-target
- knowledge-pack
- maritime
- open-harness-hub
- retrieval
- security
- transportation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Osha Injury Recordkeeping And Reporting Decisions
---

# Osha Injury Recordkeeping And Reporting Decisions

<!-- Generated from OpenHubForAI manifest `knowledge-pack/osha-injury-recordkeeping-and-reporting-decisions` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misapply 29 CFR 1904 recordability + 8h fatality / 24h amputation reporting triggers Grounded in OSHA 29 CFR 1904 + Letters of Interpretation (public domain) via classifier retrieval. Lift: deterministic decision tree + exhaustive first-aid list + exact reporting clocks

**Industries**: security, cyber, transportation, maritime, compliance, government
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
| `data/esoteric-packs/osha-injury-recordkeeping-and-reporting-decisions.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: OSHA 29 CFR 1904 + Letters of Interpretation (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/osha-injury-recordkeeping-and-reporting-decisions.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{osha-injury-recordkeeping-and-reporting-decisions_open_harness_hub,
  title  = {Osha Injury Recordkeeping And Reporting Decisions},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/osha-injury-recordkeeping-and-reporting-decisions},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/osha-injury-recordkeeping-and-reporting-decisions`.
