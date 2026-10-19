---
name: verification-packet-to-postgres-jsonl
description: Convert a grounded-search, model-review, and expert-review verification
  packet into canonical source, object, entity, dedupe, review, and index JSONL shards
  that can be loaded into Postgres/pgvector.
when_to_use: 'Pipeline kind: research_web.verification_packet_persistence.'
---

# Verification packet to Postgres JSONL

Exports high-risk verification packets into canonical JSONL row families, validates row relationships, and prepares Postgres/pgvector bulk-load inputs.

## Task

Convert a grounded-search, model-review, and expert-review verification packet into canonical source, object, entity, dedupe, review, and index JSONL shards that can be loaded into Postgres/pgvector.

## Steps

1. **govern-verification-packet** — `tool` → `tool/source-record-governance-router`
2. **export-jsonl-row-families** — `tool` → `tool/verification-packet-jsonl-exporter`
3. **preflight-row-relationships** — `tool` → `tool/factory-jsonl-relationship-preflight`
4. **prepare-bulk-copy** — `tool` → `tool/factory-jsonl-bulk-copy-loader`

## Defaults

- **knowledge_packs**: `knowledge-pack/verification-packet-record-persistence-patterns`, `knowledge-pack/expert-email-grounded-verification-patterns`

## Success criteria

- semantic must_cover ['source_record', 'normalized_object', 'canonical_entity', 'dedupe_cluster', 'review_ticket', 'index_record'] against `$.row_counts`
- deterministic `$.jsonl_files` is_truthy `True`

## Provenance

- Hub component: `pipeline/verification-packet-to-postgres-jsonl` v0.1.0
- License: `MIT`
- Industry: ai, government, humanitarian, legal, healthcare, cross_industry
- Full source manifest: see `references/manifest.yaml`
