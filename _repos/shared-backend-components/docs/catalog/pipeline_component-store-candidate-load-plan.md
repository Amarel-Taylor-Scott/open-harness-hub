# Component store candidate load plan

*pipeline* · `pipeline/component-store-candidate-load-plan` · v0.1.0 · experimental

Creates CSV and SQL load bundles that place generated components and subcomponents into Postgres candidate tables while preserving review gates and source provenance.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, serving, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a review-gated Postgres load plan for generated component and subcomponent candidates.

**pipeline_kind:** `research_web.component_store_candidate_load_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-component-store-checks` | knowledge_pack | `knowledge-pack/component-store-load-patterns` | - |
| 2 | `plan-component-store-load` | tool | `tool/component-store-load-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

