# Costed blueprint route matrix

*pipeline* · `pipeline/costed-blueprint-route-matrix` · v0.1.0 · experimental

Composes model routing, active pricing, cloud runtime pricing, guardrails, and A/B test planning into comparable deployment options for a sentence-to-pipeline SaaS request.

| axis | value |
|---|---|
| industry | ai, software.devops, government, finance, humanitarian, cross_industry |
| capability | planning, routing, evaluation, governance |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Build cheap, balanced, quality-first, and local-first blueprint options with guardrails, pricing snapshots, runtime estimates, and A/B cost-quality evaluation arms.

**pipeline_kind:** `meta_build.costed_blueprint`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `route-models` | tool | `tool/model-capability-router` | - |
| 2 | `lookup-model-pricing` | tool | `tool/model-pricing-lookup` | - |
| 3 | `lookup-runtime-pricing` | tool | `tool/cloud-runtime-pricing-lookup` | - |
| 4 | `build-route-matrix` | tool | `tool/blueprint-route-matrix-builder` | - |
| 5 | `plan-cost-quality-ab` | tool | `tool/blueprint-ab-cost-quality-planner` | - |
| 6 | `emit-terraform-placeholder` | tool | `tool/terraform-blueprint-emitter` | - |

