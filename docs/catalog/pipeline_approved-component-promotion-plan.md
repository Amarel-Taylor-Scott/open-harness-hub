# Approved component promotion plan

*pipeline* · `pipeline/approved-component-promotion-plan` · v0.1.0 · experimental

Creates CSV and SQL load bundles that move only review-approved component candidates into active Postgres component, component version, and subcomponent rows.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | evaluation, governance, routing, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a review-gated Postgres load plan for active components, versions, subcomponents, and candidate state transitions.

**pipeline_kind:** `research_web.approved_component_promotion_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-approved-promotion-checks` | knowledge_pack | `knowledge-pack/approved-component-promotion-patterns` | - |
| 2 | `plan-approved-component-promotion` | tool | `tool/approved-component-promotion-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

