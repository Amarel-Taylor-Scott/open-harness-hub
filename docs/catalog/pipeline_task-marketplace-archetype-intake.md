# Task marketplace archetype intake

*pipeline* · `pipeline/task-marketplace-archetype-intake` · v0.1.0 · experimental

Turn task-marketplace metadata or user exports into reusable task archetype primitives with privacy gates, entity records, dedupe clusters, index records, and review tickets.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | extraction, planning, governance, routing, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Normalize task-marketplace metadata into reusable workflow primitives while preserving privacy, provenance, license review, dedupe, index, and review-ticket boundaries.

**pipeline_kind:** `research_web.task_marketplace_archetype_intake`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_task_marketplace_patterns` | knowledge_pack | `knowledge-pack/task-marketplace-archetype-patterns` | - |
| 2 | `source_governance` | tool | `tool/source-record-governance-router` | - |
| 3 | `normalize_archetypes` | tool | `tool/task-marketplace-archetype-normalizer` | - |
| 4 | `entity_linking` | tool | `tool/entity-recognition-linker` | - |
| 5 | `dedupe` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 6 | `emit_index_records` | tool | `tool/index-record-emitter` | - |
| 7 | `review_routing` | processor | `processor/audit-trace-emitter` | - |

