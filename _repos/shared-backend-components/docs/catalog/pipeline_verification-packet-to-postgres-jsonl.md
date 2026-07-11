# Verification packet to Postgres JSONL

*pipeline* · `pipeline/verification-packet-to-postgres-jsonl` · v0.1.0 · experimental

Exports high-risk verification packets into canonical JSONL row families, validates row relationships, and prepares Postgres/pgvector bulk-load inputs.

| axis | value |
|---|---|
| industry | ai, government, humanitarian, legal, healthcare, cross_industry |
| capability | verification, format_conversion, retrieval, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Convert a grounded-search, model-review, and expert-review verification packet into canonical source, object, entity, dedupe, review, and index JSONL shards that can be loaded into Postgres/pgvector.

**pipeline_kind:** `research_web.verification_packet_persistence`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-verification-packet` | tool | `tool/source-record-governance-router` | - |
| 2 | `export-jsonl-row-families` | tool | `tool/verification-packet-jsonl-exporter` | - |
| 3 | `preflight-row-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 4 | `prepare-bulk-copy` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |

