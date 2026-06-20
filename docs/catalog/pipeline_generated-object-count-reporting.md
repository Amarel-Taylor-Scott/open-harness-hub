# Generated object count reporting

*pipeline* · `pipeline/generated-object-count-reporting` · v0.1.0 · experimental

Separates curated manifest count, staged JSONL rows, and canonical Postgres object rows before reporting progress toward million-object scale.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, evaluation, serving |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Report Open Harness Hub scale metrics without confusing YAML manifests with generated database objects.

**pipeline_kind:** `evaluate`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `count-staged-jsonl` | tool | `tool/object-count-report-generator` | - |
| 2 | `count-canonical-postgres` | tool | `tool/postgres-object-count-sql` | database_url is present |
| 3 | `route-missing-db-review` | tool | `tool/source-record-governance-router` | database_url is absent |

