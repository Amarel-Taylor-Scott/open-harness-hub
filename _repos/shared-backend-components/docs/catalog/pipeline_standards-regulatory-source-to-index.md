# Standards regulatory source to index

*pipeline* · `pipeline/standards-regulatory-source-to-index` · v0.1.0 · experimental

Prioritize standards and regulatory source surfaces, route governance, link entities, dedupe extracted objects, and emit source-backed index records for procedure and fact factories.

| axis | value |
|---|---|
| industry | ai, government, legal, healthcare.public_health, finance, software.devops, cross_industry |
| capability | retrieval, verification, governance, planning, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Turn prioritized standards and regulatory surfaces into governed, entity-linked, deduplicated, index-ready source and object records.

**pipeline_kind:** `research_web.standards_regulatory_source_index_build`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_source_map` | knowledge_pack | `knowledge-pack/standards-regulatory-source-map` | - |
| 2 | `prioritize_sources` | tool | `tool/source-surface-prioritizer` | - |
| 3 | `governance_entity_dedupe_index` | pipeline | `pipeline/source-governance-entity-dedupe-index` | - |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | - |

