# Factory JSONL to Postgres store

*pipeline* · `pipeline/factory-jsonl-to-postgres-store` · v0.1.0 · experimental

Move validated object-factory JSONL outputs into the canonical Postgres and pgvector-backed operational store through deterministic upsert SQL.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Emit reviewable Postgres upsert SQL from validated object-factory JSONL shards so generated objects are stored canonically rather than left only as files.

**pipeline_kind:** `research_web.factory_jsonl_to_postgres_store`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_storage_patterns` | knowledge_pack | `knowledge-pack/generated-object-storage-patterns` | - |
| 2 | `emit_postgres_upserts` | tool | `tool/factory-jsonl-postgres-loader` | - |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | - |

