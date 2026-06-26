---
license: CC-BY-4.0
tags:
- bulk-load
- construction
- cross_industry
- embedding
- energy
- evaluation
- experimental
- finance
- governance
- government
- healthcare
- media
- open-harness-hub
- pgvector
- postgres
- promotion-scoring
- public-sources
- retrieval
- review-gates
- serving
- software
task_categories:
- sentence-similarity
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Public source load plan patterns
---

# Public source load plan patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/public-source-load-plan-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Stage contracts for turning public-source replay row families into preflighted, promotion-scored, bulk-load-ready Postgres and pgvector inputs.

**Industries**: government, software, media, construction, energy, finance, healthcare, cross_industry
**Capabilities**: governance, retrieval, evaluation, serving, embedding
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `public_source_load_stage`
- `bulk_copy_contract`
- `promotion_scoring_contract`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/public-source-load-plan-patterns/stages.jsonl` | jsonl | public_source_load_stage |

## Provenance

- **sources**: OpenHubForAI public-source replay and factory bulk-load tooling
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: stage metadata only; no raw public-source captures or PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/public-source-load-plan-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{public-source-load-plan-patterns_open_harness_hub,
  title  = {Public source load plan patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/public-source-load-plan-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/public-source-load-plan-patterns`.
