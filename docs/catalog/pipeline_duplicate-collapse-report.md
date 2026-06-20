# Duplicate collapse report

*pipeline* · `pipeline/duplicate-collapse-report` · v0.1.0 · experimental

Reports staged row-family duplicate collapse before load audit, index coverage repair, promotion readiness, or Postgres loading.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, verification, evaluation, planning |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Detect duplicate primary-key collapse in staged component row families and distinguish shared reference rows from critical component candidate collisions.

**pipeline_kind:** `research_web.duplicate_collapse_report`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-duplicate-collapse-patterns` | knowledge_pack | `knowledge-pack/duplicate-collapse-report-patterns` | - |
| 2 | `report-duplicate-collapse` | tool | `tool/duplicate-collapse-reporter` | - |
| 3 | `route-conflicts` | tool | `tool/object-factory-job-router` | - |

