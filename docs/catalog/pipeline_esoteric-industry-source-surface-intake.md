# Esoteric industry source surface intake

*pipeline* · `pipeline/esoteric-industry-source-surface-intake` · v0.1.0 · experimental

Normalizes esoteric vertical source-surface seeds for automotive, employment agencies, plumbing and HVAC, woodworking, offshore oil and gas, and environmental reviews into candidate primitive plans.

| axis | value |
|---|---|
| industry | automotive, energy, manufacturing, construction, government, cross_industry |
| capability | extraction, classification, retrieval, governance, evaluation |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Turn esoteric industry source-surface seeds into governed candidate primitive plans with flexible labels and review routing.

**pipeline_kind:** `research_web.esoteric_industry_source_surface_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-source-surface-seeds` | tool | `tool/source-record-governance-router` | - |
| 2 | `normalize-source-surfaces` | tool | `tool/esoteric-source-surface-normalizer` | - |
| 3 | `emit-candidate-index` | tool | `tool/index-record-emitter` | - |
| 4 | `export-factory-rows` | tool | `tool/source-surface-seed-row-exporter` | - |

