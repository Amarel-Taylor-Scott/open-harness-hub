# Component CDC versioning

*pipeline* · `pipeline/component-cdc-versioning` · v0.1.0 · experimental

Compare component version rows, compute canonical hashes, record immutable change events, emit freshness and graph index records, and route risky updates to review.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, verification, retrieval, evaluation |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create immutable component change records and derived index/review rows whenever a component definition or source-backed fact changes.

**pipeline_kind:** `research_web.component_cdc_versioning`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `route_source_governance` | tool | `tool/source-record-governance-router` | - |
| 2 | `plan_change_events` | tool | `tool/component-cdc-planner` | - |
| 3 | `emit_index_deltas` | tool | `tool/index-record-emitter` | - |
| 4 | `route_review` | tool | `tool/source-record-governance-router` | - |

