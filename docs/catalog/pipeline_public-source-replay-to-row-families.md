# Public source replay to row families

*pipeline* · `pipeline/public-source-replay-to-row-families` · v0.1.0 · experimental

Converts replayed public-source scan jobs into schema-shaped JSONL row families, runs relationship preflight, and prepares the shards for Postgres/pgvector bulk loading.

| axis | value |
|---|---|
| industry | automotive, energy, manufacturing, construction, government, cross_industry |
| capability | extraction, classification, retrieval, governance, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Emit canonical row-family JSONL from public-source replay records and verify relational integrity before bulk load.

**pipeline_kind:** `research_web.public_source_replay_row_families`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-replay-records` | tool | `tool/source-record-governance-router` | - |
| 2 | `emit-row-families` | tool | `tool/public-source-replay-row-emitter` | - |
| 3 | `preflight-row-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |

