---
name: embedding-committed-load-audit
description: Gate tenant-visible vector search on committed Postgres object_embedding
  counts after embedding load planning.
when_to_use: 'Pipeline kind: research_web.embedding_committed_load_audit.'
---

# Embedding committed load audit

Compares planned embeddings, stored vectors, pgvector load evidence, and Postgres committed counts to gate vector search readiness.

## Task

Gate tenant-visible vector search on committed Postgres object_embedding counts after embedding load planning.

## Steps

1. **load-embedding-commit-checks** — `knowledge_pack` → `knowledge-pack/embedding-committed-load-audit-patterns`
2. **audit-embedding-committed-load** — `tool` → `tool/embedding-committed-load-auditor`

## Defaults

- **knowledge_packs**: `knowledge-pack/embedding-committed-load-audit-patterns`

## Success criteria

- deterministic `$.audit-embedding-committed-load.audit_status` in `['verified', 'load_planned_not_committed']`
- semantic must_cover ['planned', 'stored', 'pgvector', 'committed counts', 'product-ready'] against `$.audit-embedding-committed-load`

## Provenance

- Hub component: `pipeline/embedding-committed-load-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
