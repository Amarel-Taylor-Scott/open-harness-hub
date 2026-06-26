---
name: postgres-pgvector-bootstrap
description: Bootstrap a canonical Postgres/pgvector store for generated OpenHubForAI
  objects and report database-backed object counts.
when_to_use: 'Pipeline kind: serving.'
---

# Postgres pgvector bootstrap

Plans and executes the canonical Postgres/pgvector bootstrap path for generated object storage, loader SQL application, and object count reporting.

## Task

Bootstrap a canonical Postgres/pgvector store for generated OpenHubForAI objects and report database-backed object counts.

## Steps

1. **plan-bootstrap** — `tool` → `tool/postgres-pgvector-bootstrap-planner`
2. **emit-loader-sql** — `tool` → `tool/factory-jsonl-postgres-loader`
3. **count-canonical-rows** — `tool` → `tool/postgres-object-count-sql` (when `database_url is present`)
4. **count-staged-rows** — `tool` → `tool/object-count-report-generator`

## Defaults

- **knowledge_packs**: `knowledge-pack/postgres-pgvector-bootstrap-patterns`, `knowledge-pack/object-count-db-bootstrap-patterns`

## Success criteria

- deterministic `$.bootstrap_plan.commands` is_truthy `True`
- semantic must_cover ['schema initialization', 'factory JSONL loader SQL', 'canonical Postgres object count report'] against `$.bootstrap_plan`

## Provenance

- Hub component: `pipeline/postgres-pgvector-bootstrap` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
