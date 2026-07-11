# Public source rows to load plan

*pipeline* · `pipeline/public-source-rows-to-load-plan` · v0.1.0 · experimental

Turns public-source replay row families into a relationship-preflighted, promotion-scored, review-routed, bulk-load-ready Postgres and pgvector load plan.

| axis | value |
|---|---|
| industry | government, software, media, construction, energy, finance, healthcare, cross_industry |
| capability | governance, evaluation, retrieval, routing, serving, embedding |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a safe additive load plan for public-source generated objects after replay row emission.

**pipeline_kind:** `research_web.public_source_load_plan`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-public-source-load` | tool | `tool/source-record-governance-router` | - |
| 2 | `emit-load-plan` | tool | `tool/public-source-load-plan-emitter` | - |
| 3 | `bulk-copy-contract` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |
| 4 | `route-review-holds` | tool | `tool/candidate-primitive-promotion-scorer` | - |

