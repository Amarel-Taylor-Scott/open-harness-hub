# Cache-assisted harness composition

*pipeline* · `pipeline/cache-assisted-harness-composition` · v0.1.0 · experimental

Uses the Open Harness Hub object database as a trajectory-fragment cache: extract solved fragments, retrieve similar subproblems, compose candidates cheaply, verify them, and fall back to stronger models when needed.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, evaluation, governance, serving |
| modality | text, structured, code |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Retrieve and verify reusable trajectory fragments so recurring harness and pipeline subproblems can be served with less model inference.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `extract-fragments` | tool | `tool/trajectory-fragment-extractor` | - |
| 2 | `retrieve-fragments` | tool | `tool/fragment-cache-retriever` | - |
| 3 | `route-model` | tool | `tool/model-capability-router` | - |
| 4 | `stitch-and-verify` | tool | `tool/cache-stitch-verify-composer` | - |
| 5 | `emit-index` | tool | `tool/index-record-emitter` | - |

