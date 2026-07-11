# Daily showcase pipeline factory

*pipeline* · `pipeline/daily-showcase-pipeline-factory` · v0.1.0 · experimental

Creates 5 to 25 preconfigured, review-ready showcase pipeline templates per day and prepares them for Postgres component-template loading.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, routing, evaluation, governance |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Generate daily off-the-shelf pipeline templates that prove how database-backed component candidates become usable product workflows.

**pipeline_kind:** `research_web.daily_showcase_pipeline_factory`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-showcase-scenarios` | knowledge_pack | `knowledge-pack/daily-showcase-pipeline-patterns` | - |
| 2 | `generate-showcase-templates` | tool | `tool/daily-showcase-pipeline-generator` | - |
| 3 | `load-plan-review` | tool | `tool/component-template-load-planner` | - |

