---
name: embedding-execution-plan
description: Turn staged object_embedding rows into auditable embedding execution
  batches without calling embedding providers.
when_to_use: 'Pipeline kind: research_web.embedding_execution_plan.'
---

# Embedding execution plan

Plans embedding batches from staged object_embedding rows, routes them by local or external model profile, estimates cost where possible, and emits completion stubs for later vector readiness audits.

## Task

Turn staged object_embedding rows into auditable embedding execution batches without calling embedding providers.

## Steps

1. **govern-embedding-inputs** — `tool` → `tool/source-record-governance-router`
2. **lookup-embedding-pricing** — `tool` → `tool/model-pricing-lookup` (when `external embedding profile is selected`)
3. **plan-embedding-batches** — `tool` → `tool/embedding-execution-planner`
4. **route-to-vector-store** — `tool` → `tool/postgres-load-execution-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/embedding-execution-patterns`

## Success criteria

- deterministic `$.embedding_execution_plan.input_embedding_rows` > `0`
- deterministic `$.embedding_execution_plan.planned_completion_rows` == `$.embedding_execution_plan.input_embedding_rows`
- semantic must_cover ['local embedding profile', 'external pricing snapshot required', 'batch id', 'text hash', 'vector stored false before execution'] against `$.embedding_execution_plan`

## Provenance

- Hub component: `pipeline/embedding-execution-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
