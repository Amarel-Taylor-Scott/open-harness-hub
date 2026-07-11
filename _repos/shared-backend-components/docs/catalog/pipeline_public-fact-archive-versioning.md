# Public fact archive versioning

*pipeline* · `pipeline/public-fact-archive-versioning` · v0.1.0 · experimental

Track volatile public facts by querying archived captures, optionally requesting new snapshots, hashing content, diffing versions, and emitting versioned knowledge objects for RAG.

| axis | value |
|---|---|
| industry | ai, government, healthcare.public_health, cross_industry |
| capability | retrieval, verification, governance, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



## Task

Create dated, archived, hashable knowledge objects for public facts so pipelines can cite the source version valid at review time.

**pipeline_kind:** `research_web.public_fact_archive_versioning`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `lookup_archived_captures` | tool | `tool/web-archive-capture-lookup` | - |
| 2 | `request_snapshot_if_allowed` | tool | `tool/web-archive-snapshot-request` | - |
| 3 | `normalize_versioned_fact` | tool | `tool/search-result-normalizer` | - |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | - |

