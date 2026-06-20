# Component template load plan

*pipeline* · `pipeline/component-template-load-plan` · v0.1.0 · experimental

Creates CSV and SQL load bundles that place off-the-shelf component pipeline templates into Postgres template tables with ordered layer-aware steps.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | planning, routing, serving, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a review-gated Postgres load plan for reusable component pipeline templates and ordered template steps.

**pipeline_kind:** `research_web.component_template_load_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-template-checks` | knowledge_pack | `knowledge-pack/component-template-load-patterns` | - |
| 2 | `plan-template-load` | tool | `tool/component-template-load-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

