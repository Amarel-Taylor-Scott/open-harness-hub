---
license: CC-BY-4.0
tags:
- capability-lift
- esoteric
- exact_id
- experimental
- ingestion-target
- knowledge-pack
- manufacturing
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
pretty_name: Obd Dtc And Iso26262 Asil Reference
---

# Obd Dtc And Iso26262 Asil Reference

<!-- Generated from Open Harness Hub manifest `knowledge-pack/obd-dtc-and-iso26262-asil-reference` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: misdecode J2012 DTCs; muddle ISO 26262 ASIL determination + UDS service ids Grounded in SAE J2012/J1979 + ISO 26262 ASIL tables + ISO 14229 UDS (public refs) via exact_id retrieval. Lift: structured code semantics + ASIL risk-graph mapping, exact safety-relevant

**Industries**: manufacturing
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
| `data/esoteric-packs/obd-dtc-and-iso26262-asil-reference.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: SAE J2012/J1979 + ISO 26262 ASIL tables + ISO 14229 UDS (public refs)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/obd-dtc-and-iso26262-asil-reference.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{obd-dtc-and-iso26262-asil-reference_open_harness_hub,
  title  = {Obd Dtc And Iso26262 Asil Reference},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/obd-dtc-and-iso26262-asil-reference},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/obd-dtc-and-iso26262-asil-reference`.
