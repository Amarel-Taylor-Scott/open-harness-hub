---
name: local-pgvector-embedding-smoke
description: Emit a reviewed local pgvector smoke execution plan for embedding load
  SQL and committed-count audits.
when_to_use: 'Pipeline kind: research_web.local_pgvector_embedding_smoke.'
---

# Local pgvector embedding smoke

Builds a side-effect-free operator plan for smoke testing embedding load SQL against the local Docker pgvector database.

## Task

Emit a reviewed local pgvector smoke execution plan for embedding load SQL and committed-count audits.

## Steps

1. **load-local-pgvector-smoke-checks** — `knowledge_pack` → `knowledge-pack/local-pgvector-embedding-smoke-patterns`
2. **plan-local-pgvector-embedding-smoke** — `tool` → `tool/local-pgvector-embedding-smoke-planner`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-pgvector-embedding-smoke-patterns`

## Success criteria

- deterministic `$.plan-local-pgvector-embedding-smoke.readiness.safe_to_smoke_apply` == `True`
- semantic must_cover ['Docker', 'pgvector', 'schema', 'load SQL', 'committed counts', 'side-effect free'] against `$.plan-local-pgvector-embedding-smoke`

## Provenance

- Hub component: `pipeline/local-pgvector-embedding-smoke` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
