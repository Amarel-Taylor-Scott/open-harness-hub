---
license: CC0-1.0
tags:
- abbreviations
- cross_industry
- experimental
- glossary
- open-harness-hub
- retrieval
task_categories:
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Common abbreviations (cross-industry sample)
---

# Common abbreviations (cross-industry sample)

<!-- Generated from Open Harness Hub manifest `knowledge-pack/common-abbreviations` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Sampled abbreviations and acronyms across healthcare, finance,
legal, security, and technology, with expansions and a context tag.
Designed for the `expand.abbreviation` processor to look up
domain-specific expansions before retrieval or model call.

**Industries**: cross_industry
**Capabilities**: retrieval
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`

## Files

| path | format | schema |
|---|---|---|
| `data/common-abbreviations.jsonl` | jsonl | — |

## Provenance

- **sources**: Public-domain glossaries
- **collected_through**: 2026-04-30

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/common-abbreviations.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{common-abbreviations_open_harness_hub,
  title  = {Common abbreviations (cross-industry sample)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/common-abbreviations},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC0-1.0`. Hub artifact: `knowledge-pack/common-abbreviations`.
