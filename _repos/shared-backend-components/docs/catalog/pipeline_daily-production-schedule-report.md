# Daily production schedule report

*pipeline* · `pipeline/daily-production-schedule-report` · v0.1.0 · experimental

Builds a trend report over daily production runs and emits the next recommended component factory command.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, governance, evaluation, generation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Compare daily component production runs and recommend whether the next run should scale, hold, rotate matrix, or prioritize gap fill.

**pipeline_kind:** `research_web.daily_production_schedule_report`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-scheduler-checks` | knowledge_pack | `knowledge-pack/daily-production-scheduler-patterns` | - |
| 2 | `build-schedule-report` | tool | `tool/daily-production-scheduler` | - |

