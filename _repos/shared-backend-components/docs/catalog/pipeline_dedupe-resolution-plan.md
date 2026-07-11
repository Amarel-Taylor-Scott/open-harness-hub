# Dedupe resolution plan

*pipeline* · `pipeline/dedupe-resolution-plan` · v0.1.0 · experimental

Creates CSV, JSONL, and SQL load bundles that resolve dedupe clusters separately from content approval and active component promotion.

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

Create a review-gated Postgres load plan for dedupe resolutions, quality index rows, review tickets, and candidate dedupe review updates.

**pipeline_kind:** `research_web.dedupe_resolution_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-dedupe-resolution-checks` | knowledge_pack | `knowledge-pack/dedupe-resolution-patterns` | - |
| 2 | `plan-dedupe-resolution` | tool | `tool/dedupe-resolution-planner` | - |
| 3 | `audit-staged-vs-committed` | tool | `tool/staged-vs-committed-load-auditor` | - |

