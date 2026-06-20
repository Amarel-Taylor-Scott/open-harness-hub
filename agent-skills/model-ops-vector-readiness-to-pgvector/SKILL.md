---
name: model-ops-vector-readiness-to-pgvector
description: Move a staged model-ops daily run from embedding work rows to pgvector-ready
  load SQL and a committed-load audit, without applying SQL or marking vector search
  product-ready.
when_to_use: 'Pipeline kind: research_web.model_ops_vector_readiness_to_pgvector.'
---

# Model ops vector readiness to pgvector

Plans embeddings, runs a local deterministic embedding worker, emits pgvector load SQL, and audits committed-load readiness for a staged model-ops daily run.

## Task

Move a staged model-ops daily run from embedding work rows to pgvector-ready load SQL and a committed-load audit, without applying SQL or marking vector search product-ready.

## Steps

1. **plan-embedding-execution** — `tool` → `tool/embedding-execution-planner`
2. **run-local-hash-worker** — `tool` → `tool/local-hash-embedding-worker`
3. **plan-pgvector-load** — `tool` → `tool/pgvector-embedding-load-planner`
4. **audit-committed-load** — `tool` → `tool/embedding-committed-load-auditor`

## Success criteria

- deterministic `$.plan-embedding-execution.planned_completion_rows` >= `1000`
- deterministic `$.run-local-hash-worker.vector_readiness.readiness_status` == `ready`
- deterministic `$.plan-pgvector-load.rejected_rows` == `0`
- deterministic `$.audit-committed-load.audit_status` == `load_planned_not_committed`

## Provenance

- Hub component: `pipeline/model-ops-vector-readiness-to-pgvector` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
