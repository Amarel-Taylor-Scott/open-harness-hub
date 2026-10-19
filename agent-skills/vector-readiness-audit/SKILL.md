---
name: vector-readiness-audit
description: Audit vector search readiness by comparing embedding completion stubs
  with stored vector metadata.
when_to_use: 'Pipeline kind: research_web.vector_readiness_audit.'
---

# Vector readiness audit

Reconciles planned embedding completion rows with stored vector metadata so hybrid search indexes can distinguish planned, missing, ready, mismatched, and orphaned vectors.

## Task

Audit vector search readiness by comparing embedding completion stubs with stored vector metadata.

## Steps

1. **load-readiness-checks** — `knowledge_pack` → `knowledge-pack/vector-readiness-audit-patterns`
2. **audit-vector-readiness** — `tool` → `tool/vector-readiness-auditor`
3. **route-missing-or-mismatched-vectors** — `tool` → `tool/object-factory-job-router`

## Defaults

- **knowledge_packs**: `knowledge-pack/vector-readiness-audit-patterns`

## Success criteria

- deterministic `$.vector_readiness_summary.planned_rows` > `0`
- deterministic `$.vector_readiness_summary.ready_rows` <= `$.vector_readiness_summary.planned_rows`
- semantic must_cover ['missing vectors', 'text hash mismatch', 'dimension mismatch', 'orphan stored vector', 'safe retry'] against `$.vector_readiness_summary`

## Provenance

- Hub component: `pipeline/vector-readiness-audit` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
