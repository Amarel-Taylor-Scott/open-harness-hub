# Cross-domain use case seed intake

*pipeline* · `pipeline/cross-domain-use-case-seed-intake` · v0.1.0 · experimental

Normalizes banking-law, jurisdictional-law, moderation, creative, brainstorming, competition-analysis, and geographic-analysis seeds into candidate primitives while excluding insurance scope.

| axis | value |
|---|---|
| industry | finance, legal, media, creative, government, cross_industry |
| capability | planning, retrieval, generation, verification, governance |
| modality | text, image, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Convert broad use-case seed surfaces into normalized candidate primitives with governance, entity linking, dedupe, indexing, and review routing.

**pipeline_kind:** `research_web.cross_domain_use_case_seed_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-use-case-seed` | tool | `tool/source-record-governance-router` | - |
| 2 | `normalize-seed` | tool | `tool/use-case-seed-normalizer` | - |
| 3 | `link-seed-entities` | tool | `tool/entity-recognition-linker` | - |
| 4 | `dedupe-seed` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 5 | `emit-seed-index` | tool | `tool/index-record-emitter` | - |

