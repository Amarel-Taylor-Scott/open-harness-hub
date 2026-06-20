# Specialized model signal intake

*pipeline* · `pipeline/specialized-model-signal-intake` · v0.1.0 · experimental

Mines task-specific model cards, model organizations, datasets, and leaderboards into governed candidate knowledge objects and pipeline primitives.

| axis | value |
|---|---|
| industry | healthcare, finance, legal, software.devops, media, security, privacy, government, cross_industry |
| capability | classification, extraction, retrieval, evaluation, routing, governance, embedding |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Turn public task-specific model context into reusable knowledge objects, eval seeds, label schemas, model replacement routes, and review tickets.

**pipeline_kind:** `research_web.specialized_model_signal_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-model-sources` | tool | `tool/source-record-governance-router` | - |
| 2 | `normalize-model-cards` | tool | `tool/specialized-model-card-normalizer` | - |
| 3 | `link-model-signal-entities` | tool | `tool/entity-recognition-linker` | - |
| 4 | `dedupe-model-signal-primitives` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 5 | `emit-model-signal-index-records` | tool | `tool/index-record-emitter` | - |

