---
license: CC-BY-4.0
tags:
- capability-lift
- compliance
- esoteric
- exact_id
- experimental
- government
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
pretty_name: Ics Nims Emergency Management Procedures
---

# Ics Nims Emergency Management Procedures

<!-- Generated from Open Harness Hub manifest `knowledge-pack/ics-nims-emergency-management-procedures` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: blur ICS form numbers, span-of-control, planning-P, unified vs single command Grounded in FEMA NIMS doctrine + ICS forms + Stafford Act (public domain) via exact_id retrieval. Lift: form-number->purpose + resource-typing exact catalog lookups; procedure-exact

**Industries**: compliance, government
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
| `data/esoteric-packs/ics-nims-emergency-management-procedures.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FEMA NIMS doctrine + ICS forms + Stafford Act (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ics-nims-emergency-management-procedures.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ics-nims-emergency-management-procedures_open_harness_hub,
  title  = {Ics Nims Emergency Management Procedures},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ics-nims-emergency-management-procedures},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ics-nims-emergency-management-procedures`.
