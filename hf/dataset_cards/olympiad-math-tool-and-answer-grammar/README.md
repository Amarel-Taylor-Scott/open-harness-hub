---
license: CC-BY-4.0
tags:
- capability-lift
- cross_industry
- esoteric
- exact_id
- experimental
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
pretty_name: Olympiad Math Tool And Answer Grammar
---

# Olympiad Math Tool And Answer Grammar

<!-- Generated from Open Harness Hub manifest `knowledge-pack/olympiad-math-tool-and-answer-grammar` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: free-generates prose, loses arithmetic + integer-mod-1000 output contract; doesn't route to SymPy Grounded in AIMO problems + answer spec + AMC/AIME keys + MATH (MIT) via exact_id retrieval. Lift: entries paired model w/ Python/SymPy + majority vote + answer regex; tool-call + grammar lifted accuracy, auto-gradable

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
| `data/esoteric-packs/olympiad-math-tool-and-answer-grammar.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: AIMO problems + answer spec + AMC/AIME keys + MATH (MIT)
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/olympiad-math-tool-and-answer-grammar.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{olympiad-math-tool-and-answer-grammar_open_harness_hub,
  title  = {Olympiad Math Tool And Answer Grammar},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/olympiad-math-tool-and-answer-grammar},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/olympiad-math-tool-and-answer-grammar`.
