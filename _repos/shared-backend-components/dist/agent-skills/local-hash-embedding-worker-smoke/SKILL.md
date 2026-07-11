---
name: local-hash-embedding-worker-smoke
description: Generate local deterministic vectors for a daily embedding execution
  sample and prove the stored rows pass vector readiness.
when_to_use: 'Pipeline kind: research_web.local_hash_embedding_worker_smoke.'
---

# Local hash embedding worker smoke

Runs a deterministic local embedding worker against a daily embedding execution sample and validates the emitted vector rows.

## Task

Generate local deterministic vectors for a daily embedding execution sample and prove the stored rows pass vector readiness.

## Steps

1. **load-local-hash-worker-checks** — `knowledge_pack` → `knowledge-pack/local-hash-embedding-worker-patterns`
2. **run-local-hash-embedding-worker** — `tool` → `tool/local-hash-embedding-worker`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-hash-embedding-worker-patterns`

## Success criteria

- deterministic `$.run-local-hash-embedding-worker.vector_readiness.readiness_status` == `ready`
- deterministic `$.run-local-hash-embedding-worker.missing_text_rows` == `0`
- semantic must_cover ['deterministic', 'local', 'vector', 'readiness', 'dimensions', 'quality boundary'] against `$.run-local-hash-embedding-worker`

## Provenance

- Hub component: `pipeline/local-hash-embedding-worker-smoke` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
