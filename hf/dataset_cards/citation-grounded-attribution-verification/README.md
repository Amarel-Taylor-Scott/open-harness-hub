---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- experimental
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
pretty_name: Citation Grounded Attribution Verification
---

# Citation Grounded Attribution Verification

<!-- Generated from Open Harness Hub manifest `knowledge-pack/citation-grounded-attribution-verification` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: fabricates references; cites passages that don't support the claim Grounded in ALCE attributed-generation (2305.14627) over open sources via rag_vector retrieval. Lift: ALCE: even strong models low citation quality; retrieve + entailment-check enforces faithful attribution

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
| `data/esoteric-packs/citation-grounded-attribution-verification.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: ALCE attributed-generation (2305.14627) over open sources
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/citation-grounded-attribution-verification.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{citation-grounded-attribution-verification_open_harness_hub,
  title  = {Citation Grounded Attribution Verification},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/citation-grounded-attribution-verification},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/citation-grounded-attribution-verification`.
