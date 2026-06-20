---
name: theory-local-postgres-smoke
description: Bridge theory-derived staged rows and vectors into reviewed local Postgres
  smoke commands.
when_to_use: 'Pipeline kind: research_web.theory_local_postgres_smoke.'
---

# Theory local Postgres smoke

Creates an operator-reviewed local pgvector execution plan for loading theory-derived component candidates and vectors, then rerunning committed-count audits.

## Task

Bridge theory-derived staged rows and vectors into reviewed local Postgres smoke commands.

## Steps

1. **build-local-postgres-smoke-plan** — `tool` → `tool/theory-local-postgres-smoke-planner`
2. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/theory-to-component-patterns`

## Success criteria

- deterministic `$.steps.build-local-postgres-smoke-plan.readiness.safe_to_apply_locally` == `True`

## Provenance

- Hub component: `pipeline/theory-local-postgres-smoke` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, security.defensive, cross_industry
- Full source manifest: see `references/manifest.yaml`
