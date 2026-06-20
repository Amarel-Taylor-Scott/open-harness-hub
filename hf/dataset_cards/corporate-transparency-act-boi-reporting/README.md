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
- legal
- maritime
- open-harness-hub
- rag_vector
- retrieval
- transportation
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Corporate Transparency Act Boi Reporting
---

# Corporate Transparency Act Boi Reporting

<!-- Generated from Open Harness Hub manifest `knowledge-pack/corporate-transparency-act-boi-reporting` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: stale CTA BOI rules after 2024-25 exemption/scope changes & shifting deadlines Grounded in FinCEN CTA BOI Final Rule 31 CFR 1010.380 + FAQs (public domain) via rag_vector retrieval. Lift: rules/deadlines changed repeatedly via litigation; any zero-shot answer likely stale

**Industries**: finance, compliance, legal, transportation, maritime
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
| `data/esoteric-packs/corporate-transparency-act-boi-reporting.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FinCEN CTA BOI Final Rule 31 CFR 1010.380 + FAQs (public domain)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/corporate-transparency-act-boi-reporting.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{corporate-transparency-act-boi-reporting_open_harness_hub,
  title  = {Corporate Transparency Act Boi Reporting},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/corporate-transparency-act-boi-reporting},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/corporate-transparency-act-boi-reporting`.
