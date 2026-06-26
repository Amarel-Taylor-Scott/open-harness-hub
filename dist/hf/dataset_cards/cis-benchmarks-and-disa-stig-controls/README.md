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
pretty_name: Cis Benchmarks And Disa Stig Controls
---

# Cis Benchmarks And Disa Stig Controls

<!-- Generated from OpenHubForAI manifest `knowledge-pack/cis-benchmarks-and-disa-stig-controls` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invent CIS recommendation numbers + DISA STIG V-IDs/severities; wrong product version Grounded in DISA STIGs (DoD public) + CIS Benchmarks (free) + SCAP/OVAL (NIST) via exact_id retrieval. Lift: control ids/severities/scope exact, audit-traceable, rapidly revised

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
| `data/esoteric-packs/cis-benchmarks-and-disa-stig-controls.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: DISA STIGs (DoD public) + CIS Benchmarks (free) + SCAP/OVAL (NIST)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cis-benchmarks-and-disa-stig-controls.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cis-benchmarks-and-disa-stig-controls_open_harness_hub,
  title  = {Cis Benchmarks And Disa Stig Controls},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cis-benchmarks-and-disa-stig-controls},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cis-benchmarks-and-disa-stig-controls`.
