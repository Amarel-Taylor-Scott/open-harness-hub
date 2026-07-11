---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- experimental
- government
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
pretty_name: Hud Section8 Hcv Occupancy Rules
---

# Hud Section8 Hcv Occupancy Rules

<!-- Generated from OpenHubForAI manifest `knowledge-pack/hud-section8-hcv-occupancy-rules` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: confuse payment-standard/FMR, 40% rent-burden cap, HQS fail items, portability Grounded in HUD 24 CFR 982 + HCV Guidebook + HQS checklist (public domain) via rag_vector retrieval. Lift: exact caps + enumerated inspection checklist, procedure-heavy

**Industries**: government
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
| `data/esoteric-packs/hud-section8-hcv-occupancy-rules.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: HUD 24 CFR 982 + HCV Guidebook + HQS checklist (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/hud-section8-hcv-occupancy-rules.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{hud-section8-hcv-occupancy-rules_open_harness_hub,
  title  = {Hud Section8 Hcv Occupancy Rules},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/hud-section8-hcv-occupancy-rules},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/hud-section8-hcv-occupancy-rules`.
