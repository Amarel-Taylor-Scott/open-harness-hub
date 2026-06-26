---
name: hybrid-postgres-bigquery-hosting-plan
description: Recommend the cheapest practical hosting split for millions of generated
  objects, trajectory fragments, embeddings, search indexes, review tickets, and cost
  traces.
when_to_use: 'Pipeline kind: serving.'
---

# Hybrid Postgres BigQuery hosting plan

Builds a low-cost hosting blueprint that keeps hot OpenHubForAI product state in Postgres/pgvector, raw shards in object storage, and cold analytics/vector workloads in BigQuery.

## Task

Recommend the cheapest practical hosting split for millions of generated objects, trajectory fragments, embeddings, search indexes, review tickets, and cost traces.

## Steps

1. **plan-postgres-bootstrap** — `tool` → `tool/postgres-pgvector-bootstrap-planner`
2. **plan-bigquery-cold-tier** — `tool` → `tool/bigquery-cold-tier-export-planner`
3. **estimate-cloud-runtime** — `tool` → `tool/cloud-runtime-pricing-lookup`
4. **emit-terraform** — `tool` → `tool/terraform-blueprint-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/hybrid-postgres-bigquery-hosting-patterns`, `knowledge-pack/postgres-pgvector-bootstrap-patterns`

## Success criteria

- semantic must_cover ['Postgres hot path', 'object storage raw shards', 'BigQuery cold analytics', 'vector search', 'cost controls'] against `$.hosting_blueprint`
- deterministic `$.cold_tier_export_plan` is_truthy `True`

## Provenance

- Hub component: `pipeline/hybrid-postgres-bigquery-hosting-plan` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
