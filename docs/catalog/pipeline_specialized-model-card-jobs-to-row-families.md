# Specialized model-card jobs to row families

*pipeline* · `pipeline/specialized-model-card-jobs-to-row-families` · v0.1.0 · experimental

Converts specialized model-card scan jobs into schema-shaped JSONL row families, runs relationship preflight, and prepares the shards for Postgres/pgvector bulk loading.

| axis | value |
|---|---|
| industry | healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry |
| capability | extraction, classification, retrieval, evaluation, routing, governance, embedding |
| modality | structured, text, image |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Emit canonical row-family JSONL from specialized model-card scan jobs and verify relational integrity before bulk load.

**pipeline_kind:** `research_web.specialized_model_card_row_families`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-model-card-scan-jobs` | tool | `tool/source-record-governance-router` | - |
| 2 | `emit-row-families` | tool | `tool/specialized-model-card-row-emitter` | - |
| 3 | `preflight-row-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |

