---
name: public-source-replay-to-row-families
description: Emit canonical row-family JSONL from public-source replay records and
  verify relational integrity before bulk load.
when_to_use: 'Pipeline kind: research_web.public_source_replay_row_families.'
---

# Public source replay to row families

Converts replayed public-source scan jobs into schema-shaped JSONL row families, runs relationship preflight, and prepares the shards for Postgres/pgvector bulk loading.

## Task

Emit canonical row-family JSONL from public-source replay records and verify relational integrity before bulk load.

## Steps

1. **govern-replay-records** — `tool` → `tool/source-record-governance-router`
2. **emit-row-families** — `tool` → `tool/public-source-replay-row-emitter`
3. **preflight-row-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`

## Defaults

- **knowledge_packs**: `knowledge-pack/public-source-job-replay-patterns`, `knowledge-pack/public-source-replay-row-patterns`

## Success criteria

- semantic must_cover ['source_record', 'normalized_object', 'canonical_entity', 'dedupe_cluster', 'index_record', 'review_ticket'] against `$.row_counts`
- deterministic `$.preflight_report.ok` == `True`

## Provenance

- Hub component: `pipeline/public-source-replay-to-row-families` v0.1.0
- License: `MIT`
- Industry: automotive, energy, manufacturing, construction, government, cross_industry
- Full source manifest: see `references/manifest.yaml`
