# Public source blueprints to scan jobs

*pipeline* · `pipeline/public-source-blueprints-to-scan-jobs` · v0.1.0 · experimental

Turns governed public-source blueprints into resumable object-factory scan jobs that can be consumed by containerized workers without embedding scraped source bodies in the catalog.

| axis | value |
|---|---|
| industry | automotive, energy, manufacturing, construction, government, cross_industry |
| capability | retrieval, extraction, governance, routing, evaluation |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Emit queue-ready scan jobs and shard manifests from public-source blueprints, with source governance and excluded-scope policy attached to every job.

**pipeline_kind:** `research_web.public_source_scan_job_emission`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-public-source-blueprint-batch` | tool | `tool/source-record-governance-router` | - |
| 2 | `normalize-blueprints` | tool | `tool/public-source-blueprint-normalizer` | - |
| 3 | `emit-scan-jobs` | tool | `tool/public-source-scan-job-emitter` | - |
| 4 | `route-emitted-jobs` | tool | `tool/object-factory-job-router` | - |

