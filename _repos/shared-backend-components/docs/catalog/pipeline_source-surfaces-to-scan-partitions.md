# Source surfaces to scan partitions

*pipeline* · `pipeline/source-surfaces-to-scan-partitions` · v0.1.0 · experimental

Turns high-value source-surface backlog rows into resumable partitions, public-source blueprints, and queue-ready scan jobs for the object factory.

| axis | value |
|---|---|
| industry | government, software, media, construction, energy, finance, healthcare, cross_industry |
| capability | retrieval, extraction, governance, routing, evaluation |
| modality | text, structured, image |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Plan additive source-surface scan partitions and route them into public-source scan jobs without storing raw source bodies in the public catalog.

**pipeline_kind:** `research_web.source_surface_partitioning`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-source-surface-backlog` | tool | `tool/source-record-governance-router` | - |
| 2 | `plan-source-surface-partitions` | tool | `tool/source-surface-partition-planner` | - |
| 3 | `emit-public-source-scan-jobs` | tool | `tool/public-source-scan-job-emitter` | - |
| 4 | `route-jobs-to-container-workers` | tool | `tool/object-factory-job-router` | - |

