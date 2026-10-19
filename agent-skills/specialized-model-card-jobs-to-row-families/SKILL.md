---
name: specialized-model-card-jobs-to-row-families
description: Emit canonical row-family JSONL from specialized model-card scan jobs
  and verify relational integrity before bulk load.
when_to_use: 'Pipeline kind: research_web.specialized_model_card_row_families.'
---

# Specialized model-card jobs to row families

Converts specialized model-card scan jobs into schema-shaped JSONL row families, runs relationship preflight, and prepares the shards for Postgres/pgvector bulk loading.

## Task

Emit canonical row-family JSONL from specialized model-card scan jobs and verify relational integrity before bulk load.

## Steps

1. **govern-model-card-scan-jobs** — `tool` → `tool/source-record-governance-router`
2. **emit-row-families** — `tool` → `tool/specialized-model-card-row-emitter`
3. **preflight-row-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`

## Defaults

- **knowledge_packs**: `knowledge-pack/specialized-model-card-scan-job-patterns`, `knowledge-pack/specialized-model-card-row-patterns`

## Success criteria

- semantic must_cover ['source_record', 'normalized_object', 'canonical_entity', 'dedupe_cluster', 'index_record', 'review_ticket'] against `$.row_counts`
- deterministic `$.preflight_report.ok` == `True`

## Provenance

- Hub component: `pipeline/specialized-model-card-jobs-to-row-families` v0.1.0
- License: `MIT`
- Industry: healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
