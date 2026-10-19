---
name: postgres-load-execution-and-audit
description: Plan execution of a generated object-factory load.sql against Postgres
  and the follow-up committed-count audit.
when_to_use: 'Pipeline kind: research_web.postgres_load_execution.'
---

# Postgres load execution and audit

Creates a side-effect-free command plan to initialize Postgres/pgvector, apply a generated bulk load, export committed counts, and audit staged versus committed object rows.

## Task

Plan execution of a generated object-factory load.sql against Postgres and the follow-up committed-count audit.

## Steps

1. **govern-load-execution-plan** — `tool` → `tool/source-record-governance-router`
2. **emit-execution-plan** — `tool` → `tool/postgres-load-execution-planner`
3. **convert-counts-after-psql** — `tool` → `tool/psql-csv-count-json-converter` (when `psql count CSV is available`)
4. **audit-after-load** — `tool` → `tool/staged-vs-committed-load-auditor` (when `committed count JSON is available`)

## Defaults

- **knowledge_packs**: `knowledge-pack/postgres-load-execution-patterns`, `knowledge-pack/staged-vs-committed-load-audit-patterns`

## Success criteria

- deterministic `$.execution_plan.readiness.preflight_ok` == `True`
- semantic must_cover ['initialize schema', 'apply bulk load', 'count canonical rows', 'audit staged versus committed'] against `$.execution_plan.commands`

## Provenance

- Hub component: `pipeline/postgres-load-execution-and-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
