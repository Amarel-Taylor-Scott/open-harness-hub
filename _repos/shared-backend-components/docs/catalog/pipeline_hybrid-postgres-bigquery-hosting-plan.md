# Hybrid Postgres BigQuery hosting plan

*pipeline* · `pipeline/hybrid-postgres-bigquery-hosting-plan` · v0.1.0 · experimental

Builds a low-cost hosting blueprint that keeps hot OpenHubForAI product state in Postgres/pgvector, raw shards in object storage, and cold analytics/vector workloads in BigQuery.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, evaluation |
| modality | text, structured, tabular |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | dated |
| license | MIT |



## Task

Recommend the cheapest practical hosting split for millions of generated objects, trajectory fragments, embeddings, search indexes, review tickets, and cost traces.

**pipeline_kind:** `serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `plan-postgres-bootstrap` | tool | `tool/postgres-pgvector-bootstrap-planner` | - |
| 2 | `plan-bigquery-cold-tier` | tool | `tool/bigquery-cold-tier-export-planner` | - |
| 3 | `estimate-cloud-runtime` | tool | `tool/cloud-runtime-pricing-lookup` | - |
| 4 | `emit-terraform` | tool | `tool/terraform-blueprint-emitter` | - |

