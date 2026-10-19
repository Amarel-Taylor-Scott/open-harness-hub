---
name: pgvector-embedding-load-plan
description: Convert completed local embedding worker vector rows into reviewable
  pgvector object_embedding load SQL.
when_to_use: 'Pipeline kind: research_web.pgvector_embedding_load_plan.'
---

# Pgvector embedding load plan

Turns stored vector JSONL rows into accepted/rejected load evidence and reviewable SQL for the canonical Postgres object_embedding table.

## Task

Convert completed local embedding worker vector rows into reviewable pgvector object_embedding load SQL.

## Steps

1. **load-pgvector-load-checks** — `knowledge_pack` → `knowledge-pack/pgvector-embedding-load-patterns`
2. **plan-pgvector-embedding-load** — `tool` → `tool/pgvector-embedding-load-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/pgvector-embedding-load-patterns`

## Success criteria

- deterministic `$.plan-pgvector-embedding-load.accepted_rows` >= `1`
- deterministic `$.plan-pgvector-embedding-load.rejected_rows` == `0`
- semantic must_cover ['pgvector', 'object_embedding', 'dimension', 'source text', 'reviewable SQL', 'side effect free'] against `$.plan-pgvector-embedding-load`

## Provenance

- Hub component: `pipeline/pgvector-embedding-load-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
