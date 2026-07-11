# Public source scan jobs to replay partitions

*pipeline* · `pipeline/public-source-scan-jobs-to-replay-partitions` · v0.1.0 · experimental

Consumes emitted public-source scan jobs and produces resumable run records, checkpoints, and partition manifests that prepare later container workers and Postgres/pgvector bulk loads.

| axis | value |
|---|---|
| industry | automotive, energy, manufacturing, construction, government, cross_industry |
| capability | routing, governance, evaluation, retrieval |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Replay public-source scan jobs into additive partition manifests and checkpoints without storing source bodies, then audit the generated partitions for later bulk-load and index replay.

**pipeline_kind:** `research_web.public_source_job_replay_partitions`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-scan-job-batch` | tool | `tool/source-record-governance-router` | - |
| 2 | `replay-scan-jobs` | tool | `tool/public-source-job-replay-runner` | - |
| 3 | `audit-replay-partitions` | tool | `tool/worker-output-merge-auditor` | - |

