# Local sentence blueprint output records

*pipeline* · `pipeline/local-sentence-blueprint-output-records` · v0.1.0 · experimental

Turns a local sentence-to-pipeline demo request into governed, normalized, deduplicated, indexed output records that can later be stored in Postgres and searched as reusable primitives.

| axis | value |
|---|---|
| industry | ai, software.devops, government, finance, humanitarian, cross_industry |
| capability | planning, routing, evaluation, governance, retrieval |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



## Task

Convert a user sentence and route matrix into normalized output records with governance, entity linking, fuzzy dedupe, index emission, and review ticket routing.

**pipeline_kind:** `meta_build.local_blueprint_records`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-source-prompt` | tool | `tool/source-record-governance-router` | - |
| 2 | `run-local-demo` | tool | `tool/sentence-to-pipeline-blueprint-runner` | - |
| 3 | `build-route-matrix` | pipeline | `pipeline/costed-blueprint-route-matrix` | - |
| 4 | `emit-output-records` | tool | `tool/blueprint-output-record-emitter` | - |
| 5 | `link-entities` | tool | `tool/entity-recognition-linker` | - |
| 6 | `dedupe-output-records` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 7 | `emit-index-records` | tool | `tool/index-record-emitter` | - |

