---
license: CC-BY-4.0
tags:
- ai
- cross_industry
- docker-compose
- evaluation
- experimental
- governance
- load-execution
- object-counts
- open-harness-hub
- pgvector
- postgres
- render
- retrieval
- serving
- software.devops
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Postgres load execution patterns
---

# Postgres load execution patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/postgres-load-execution-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Step contracts for applying a generated object-factory load plan to local, Render, or managed Postgres with pgvector, then counting and auditing committed rows.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, retrieval, serving, evaluation, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `postgres_load_execution_step`
- `pgvector_load_audit_step`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/postgres-load-execution-patterns/steps.jsonl` | jsonl | postgres_load_execution_step |

## Provenance

- **sources**: db/postgres/schema.sql, db/postgres/object_count_report.sql, infra/postgres/docker-compose.pgvector.yml
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: execution metadata only; no database credentials or source bodies

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/postgres-load-execution-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{postgres-load-execution-patterns_open_harness_hub,
  title  = {Postgres load execution patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/postgres-load-execution-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/postgres-load-execution-patterns`.
