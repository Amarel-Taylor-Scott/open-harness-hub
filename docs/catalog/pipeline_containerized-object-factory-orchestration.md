# Containerized object factory orchestration

*pipeline* · `pipeline/containerized-object-factory-orchestration` · v0.1.0 · experimental

Plans and audits a horizontally scalable worker fleet for source discovery, scraping, spidering, repository/workflow mining, enrichment, embedding, verification, promotion, warehouse export, and prompt-prefix cache savings.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, retrieval, extraction, verification, routing, serving |
| modality | text, structured, code, image, tabular |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Split Open Harness Hub object generation into parallel container worker lanes with source governance, shard leasing, enrichment, validation, promotion, warehouse export, and prompt-prefix cache normalization.

**pipeline_kind:** `research_web.object_factory_worker_fleet`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `source-governance` | tool | `tool/source-record-governance-router` | - |
| 2 | `plan-shards` | tool | `tool/container-worker-shard-planner` | - |
| 3 | `route-worker-jobs` | tool | `tool/object-factory-job-router` | - |
| 4 | `normalize-prompt-prefix` | tool | `tool/prompt-prefix-cache-normalizer` | - |
| 5 | `export-cold-tier-plan` | tool | `tool/bigquery-cold-tier-export-planner` | - |
| 6 | `merge-audit` | tool | `tool/worker-output-merge-auditor` | - |

