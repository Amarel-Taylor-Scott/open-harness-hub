# Multimodal public service harness intake

*pipeline* · `pipeline/multimodal-public-service-harness-intake` · v0.1.0 · experimental

Normalizes disaster assistance, water quality, and food quality use cases into multi-model harnesses, generated row shards, source-governed facts, review tickets, and index records.

| axis | value |
|---|---|
| industry | humanitarian.disaster, government.benefits, environmental.water, water_utility.sdwa, food.safety, food_safety |
| capability | governance, retrieval, verification, evaluation |
| modality | text, image, structured, tabular, spatial, timeseries, multimodal |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Convert public-service and quality use cases into reusable multimodal harness primitives and generated database rows.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `source-governance` | tool | `tool/source-record-governance-router` | - |
| 2 | `route-evidence` | tool | `tool/multimodal-evidence-router` | - |
| 3 | `model-route` | tool | `tool/model-capability-router` | - |
| 4 | `disaster-assistance` | harness | `harness/disaster-assistance-multimodal-intake` | domain == humanitarian.disaster |
| 5 | `water-quality` | harness | `harness/water-quality-multimodal-triage` | domain == environmental.water |
| 6 | `food-quality` | harness | `harness/food-quality-multimodal-hold-release` | domain == food.safety |
| 7 | `safety-screen` | tool | `tool/multimodal-safety-screen` | - |
| 8 | `emit-index` | tool | `tool/index-record-emitter` | - |

