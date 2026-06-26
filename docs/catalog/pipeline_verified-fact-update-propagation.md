# Verified fact update propagation

*pipeline* · `pipeline/verified-fact-update-propagation` · v0.1.0 · experimental

Ingests a signed verified fact update from a vetted publisher, updates source-governed knowledge records, finds dependent pipelines, emits review tickets, and prepares re-index or redeployment plans.

| axis | value |
|---|---|
| industry | ai, government, legal, cross_industry |
| capability | verification, governance, retrieval, planning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Propagate vetted source-of-truth updates such as government rule changes into dependent OpenHubForAI pipelines and indexes.

**pipeline_kind:** `research_web.verified_fact_update`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `verify-publisher-submission` | tool | `tool/verified-source-publisher-intake` | - |
| 2 | `signed-object-intake` | tool | `tool/signed-knowledge-object-intake` | - |
| 3 | `index-signed-knowledge` | pipeline | `pipeline/signed-knowledge-object-to-index` | - |
| 4 | `propagate-impact` | tool | `tool/verified-fact-impact-propagator` | - |
| 5 | `emit-index-delta` | tool | `tool/index-record-emitter` | - |

