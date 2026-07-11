# Specialized model signals to scan jobs

*pipeline* · `pipeline/specialized-model-signals-to-scan-jobs` · v0.1.0 · experimental

Turns specialized model signal rows into resumable object-factory jobs that mine model-card context into reusable primitive candidates without downloading model weights.

| axis | value |
|---|---|
| industry | healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry |
| capability | retrieval, extraction, classification, evaluation, routing, governance, embedding |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Emit queue-ready model-card scan jobs and shard manifests from specialized model signal rows, with governance and excluded-scope policy attached to every job.

**pipeline_kind:** `research_web.specialized_model_card_scan_job_emission`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-specialized-model-signal-batch` | tool | `tool/source-record-governance-router` | - |
| 2 | `emit-model-card-scan-jobs` | tool | `tool/specialized-model-card-scan-job-emitter` | - |
| 3 | `route-emitted-model-card-jobs` | tool | `tool/object-factory-job-router` | - |

