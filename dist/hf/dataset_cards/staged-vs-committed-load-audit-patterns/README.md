---
license: CC-BY-4.0
tags:
- ai
- bulk-load
- cross_industry
- evaluation
- experimental
- governance
- load-audit
- object-counts
- open-harness-hub
- pgvector
- postgres
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
pretty_name: Staged versus committed load audit patterns
---

# Staged versus committed load audit patterns

<!-- Generated from OpenHubForAI manifest `knowledge-pack/staged-vs-committed-load-audit-patterns` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Relation-level checks for comparing staged object-factory bulk-load counts against canonical Postgres and pgvector row counts after load execution.

**Industries**: ai, software.devops, cross_industry
**Capabilities**: governance, evaluation, retrieval, serving, verification
**Modalities**: structured, text
**Freshness**: stable
**Trust boundary**: local

## Content types (leaf vocabulary)

- `load_audit_check`
- `postgres_count_reconciliation`

## Files

| path | format | schema |
|---|---|---|
| `catalog/knowledge-packs/data/staged-vs-committed-load-audit-patterns/checks.jsonl` | jsonl | load_audit_check |

## Provenance

- **sources**: db/postgres/object_count_report.sql, OpenHubForAI bulk load manifests
- **collected_through**: 2026-05-25
- **collected_by**: OpenHubForAI contributors
- **anonymization**: count reconciliation metadata only; no source bodies or PII

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/staged-vs-committed-load-audit-patterns.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{staged-vs-committed-load-audit-patterns_open_harness_hub,
  title  = {Staged versus committed load audit patterns},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/staged-vs-committed-load-audit-patterns},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/staged-vs-committed-load-audit-patterns`.
