---
name: daily-partitions-to-postgres-load-audit
description: Prepare multiple daily component candidate partitions for canonical Postgres/pgvector
  staging without overcounting duplicate source and entity rows.
when_to_use: 'Pipeline kind: research_web.daily_partition_load_audit.'
---

# Daily partitions to Postgres load audit

Merges daily component candidate partitions into deduplicated JSONL, checks local relationships, emits psql bulk COPY files, and records the staged proof boundary before a Postgres load.

## Task

Prepare multiple daily component candidate partitions for canonical Postgres/pgvector staging without overcounting duplicate source and entity rows.

## Steps

1. **load-audit-patterns** — `knowledge_pack` → `knowledge-pack/daily-partition-load-audit-patterns`
2. **merge-preflight-and-export** — `tool` → `tool/daily-partition-load-auditor`
3. **operator-runs-postgres-load** — `tool` → `tool/postgres-load-execution-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/daily-partition-load-audit-patterns`, `knowledge-pack/daily-thousand-component-factory-patterns`

## Success criteria

- deterministic `$.merge-preflight-and-export.preflight.ok` == `True`
- deterministic `$.merge-preflight-and-export.bulk_manifest.load_sql` is_truthy `True`
- semantic must_cover ['deduplicates by primary key', 'staged_only until committed Postgres counts are supplied', 'keeps YAML definition count separate from database row count'] against `$.merge-preflight-and-export`

## Provenance

- Hub component: `pipeline/daily-partitions-to-postgres-load-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
