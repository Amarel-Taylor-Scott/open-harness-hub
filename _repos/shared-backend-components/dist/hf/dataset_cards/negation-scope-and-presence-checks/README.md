---
license: CC-BY-4.0
tags:
- capability-lift
- classifier
- cross_industry
- esoteric
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
pretty_name: Negation Scope And Presence Checks
---

# Negation Scope And Presence Checks

<!-- Generated from OpenHubForAI manifest `knowledge-pack/negation-scope-and-presence-checks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Capability-lift knowledge pack for an esoteric area LLMs handle poorly. Gap: ignores not/never/without; confuses negated vs affirmed findings Grounded in 'This is not a Dataset' (2310.15941) + negation NLI sets via classifier retrieval. Lift: Language models are not naysayers (2306.08189): poor negation; scope detector prevents polarity flips

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
| `data/esoteric-packs/negation-scope-and-presence-checks.jsonl` | jsonl | capability-gap seed (real facts where stable; else ingestion contract) |

## Provenance

- **sources**: 'This is not a Dataset' (2310.15941) + negation NLI sets
- **collected_through**: 2026-05-28
- **collected_by**: capability-gap factory

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/negation-scope-and-presence-checks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{negation-scope-and-presence-checks_open_harness_hub,
  title  = {Negation Scope And Presence Checks},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/negation-scope-and-presence-checks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/negation-scope-and-presence-checks`.
