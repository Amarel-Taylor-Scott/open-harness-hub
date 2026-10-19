---
license: CC-BY-4.0
tags:
- capability-lift
- cyber
- esoteric
- exact_id
- experimental
- infrastructure
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
pretty_name: Ietf Rfc And Iana Protocol Registries
---

# Ietf Rfc And Iana Protocol Registries

<!-- Generated from Open Harness Hub manifest `knowledge-pack/ietf-rfc-and-iana-protocol-registries` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: invent RFC numbers, miss obsoletes/updates, fabricate IANA ports/code-points Grounded in IETF RFC index (TLP-redistributable) + IANA registries (public) via exact_id retrieval. Lift: obsoletes/updates graph + exact code-point assignments, continually revised

**Industries**: infrastructure, cyber
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
| `data/esoteric-packs/ietf-rfc-and-iana-protocol-registries.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: IETF RFC index (TLP-redistributable) + IANA registries (public)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/ietf-rfc-and-iana-protocol-registries.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{ietf-rfc-and-iana-protocol-registries_open_harness_hub,
  title  = {Ietf Rfc And Iana Protocol Registries},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/ietf-rfc-and-iana-protocol-registries},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/ietf-rfc-and-iana-protocol-registries`.
