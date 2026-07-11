# Daily partitions to Postgres load audit

*pipeline* · `pipeline/daily-partitions-to-postgres-load-audit` · v0.1.0 · experimental

Merges daily component candidate partitions into deduplicated JSONL, checks local relationships, emits psql bulk COPY files, and records the staged proof boundary before a Postgres load.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, serving, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Prepare multiple daily component candidate partitions for canonical Postgres/pgvector staging without overcounting duplicate source and entity rows.

**pipeline_kind:** `research_web.daily_partition_load_audit`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-audit-patterns` | knowledge_pack | `knowledge-pack/daily-partition-load-audit-patterns` | - |
| 2 | `merge-preflight-and-export` | tool | `tool/daily-partition-load-auditor` | - |
| 3 | `operator-runs-postgres-load` | tool | `tool/postgres-load-execution-planner` | - |

