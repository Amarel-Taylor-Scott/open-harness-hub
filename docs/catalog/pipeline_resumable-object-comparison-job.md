# Resumable object comparison job

*pipeline* · `pipeline/resumable-object-comparison-job` · v0.1.0 · experimental

Plans blocked knowledge-object pairwise comparison leaves from normalized objects plus optional labels, dimensions, entity refs, and embedding buckets, compares leaf shards, emits checkpoints, and resumes without recomparing completed pairs.

| axis | value |
|---|---|
| industry | ai, software.devops, government, cross_industry |
| capability | retrieval, governance, evaluation, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Compare large sets of knowledge objects using blocking, leaf shards, and checkpoints so workers can resume record-by-record comparisons across runs.

**pipeline_kind:** `research_web.resumable_object_comparison`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-record-set` | tool | `tool/source-record-governance-router` | - |
| 2 | `plan-blocked-leaves` | tool | `tool/object-comparison-block-planner` | - |
| 3 | `compare-one-leaf` | tool | `tool/object-comparison-leaf-worker` | - |
| 4 | `dedupe-comparison-candidates` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 5 | `emit-comparison-index` | tool | `tool/index-record-emitter` | - |

