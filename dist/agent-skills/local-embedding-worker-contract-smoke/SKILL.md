---
name: local-embedding-worker-contract-smoke
description: Prove a local embedding worker can produce database-loadable vector metadata
  rows for a daily embedding execution sample.
when_to_use: 'Pipeline kind: research_web.local_embedding_worker_contract_smoke.'
---

# Local embedding worker contract smoke

Runs a bounded local worker contract check that proves stored vector metadata rows line up with daily embedding completion stubs.

## Task

Prove a local embedding worker can produce database-loadable vector metadata rows for a daily embedding execution sample.

## Steps

1. **load-local-embedding-contract-checks** — `knowledge_pack` → `knowledge-pack/local-embedding-worker-contract-patterns`
2. **run-local-embedding-worker-contract** — `tool` → `tool/local-embedding-worker-contract`

## Defaults

- **knowledge_packs**: `knowledge-pack/local-embedding-worker-contract-patterns`

## Success criteria

- deterministic `$.run-local-embedding-worker-contract.vector_readiness.readiness_status` == `ready`
- deterministic `$.run-local-embedding-worker-contract.stored_vector_rows` >= `1`
- semantic must_cover ['contract stub', 'embedding id', 'text hash', 'dimensions', 'readiness', 'not production vectors'] against `$.run-local-embedding-worker-contract`

## Provenance

- Hub component: `pipeline/local-embedding-worker-contract-smoke` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
