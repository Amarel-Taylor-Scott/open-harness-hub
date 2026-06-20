# Public source blueprint intake

*pipeline* · `pipeline/public-source-blueprint-intake` · v0.1.0 · experimental

Turns public source blueprints for esoteric verticals into governed scan, archive, conversion, extraction, entity-linking, dedupe, indexing, and review plans.

| axis | value |
|---|---|
| industry | automotive, energy, manufacturing, construction, government, cross_industry |
| capability | retrieval, extraction, classification, governance, evaluation |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



## Task

Create governed public-source scan and normalization jobs for source families that can generate candidate primitives at scale.

**pipeline_kind:** `research_web.public_source_blueprint_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-public-source-blueprints` | tool | `tool/source-record-governance-router` | - |
| 2 | `normalize-blueprints` | tool | `tool/public-source-blueprint-normalizer` | - |
| 3 | `scan-source-surface` | tool | `tool/primitive-source-surface-scanner` | - |
| 4 | `capture-archive` | tool | `tool/web-archive-capture-lookup` | - |
| 5 | `convert-page` | tool | `tool/page-to-markdown-converter` | - |
| 6 | `extract-normalized-objects` | tool | `tool/normalized-object-extractor` | - |
| 7 | `link-entities` | tool | `tool/entity-recognition-linker` | - |
| 8 | `dedupe-objects` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 9 | `emit-index-records` | tool | `tool/index-record-emitter` | - |

