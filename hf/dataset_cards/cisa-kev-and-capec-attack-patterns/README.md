---
license: CC-BY-4.0
tags:
- capability-lift
- cyber
- esoteric
- exact_id
- experimental
- ingestion-target
- knowledge-pack
- open-harness-hub
- retrieval
- security
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cisa Kev And Capec Attack Patterns
---

# Cisa Kev And Capec Attack Patterns

<!-- Generated from Open Harness Hub manifest `knowledge-pack/cisa-kev-and-capec-attack-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: don't know CISA KEV membership/due-dates; confuse CAPEC vs ATT&CK ids Grounded in CISA KEV (public domain) + MITRE CAPEC (free) via exact_id retrieval. Lift: continuously-updated catalog with binding federal remediation deadlines

**Industries**: security, cyber
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
| `data/esoteric-packs/cisa-kev-and-capec-attack-patterns.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: CISA KEV (public domain) + MITRE CAPEC (free)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cisa-kev-and-capec-attack-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cisa-kev-and-capec-attack-patterns_open_harness_hub,
  title  = {Cisa Kev And Capec Attack Patterns},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cisa-kev-and-capec-attack-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cisa-kev-and-capec-attack-patterns`.
