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
pretty_name: Fast Changing World Facts With Asof Dates
---

# Fast Changing World Facts With Asof Dates

<!-- Generated from Open Harness Hub manifest `knowledge-pack/fast-changing-world-facts-with-asof-dates` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: stale post-cutoff answers; fails false-premise time questions; no as-of date Grounded in FreshQA living benchmark schema on Wikidata + dated sources via rag_vector retrieval. Lift: FreshLLMs (2310.03214): all LLMs degrade on fast-changing/false-premise; dated retrieval closes it

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
| `data/esoteric-packs/fast-changing-world-facts-with-asof-dates.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: FreshQA living benchmark schema on Wikidata + dated sources
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/fast-changing-world-facts-with-asof-dates.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{fast-changing-world-facts-with-asof-dates_open_harness_hub,
  title  = {Fast Changing World Facts With Asof Dates},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/fast-changing-world-facts-with-asof-dates},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/fast-changing-world-facts-with-asof-dates`.
