# Use case seeds to entity ref rows

*pipeline* · `pipeline/use-case-seeds-to-entity-ref-rows` · v0.1.0 · experimental

Promotes cross-domain use-case seed domains, flexible label paths, inputs, outputs, required stages, and risk tiers into canonical entity and object_entity_ref rows for graph search and comparison blocking.

| axis | value |
|---|---|
| industry | ai, software.devops, finance, legal, media, creative, energy, healthcare, cross_industry |
| capability | extraction, retrieval, classification, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



## Task

Convert cross-domain use-case seed metadata into canonical entity and object_entity_ref rows that can drive graph search, blocking, dedupe, and pipeline assembly.

**pipeline_kind:** `research_web.use_case_seed_entity_ref_rows`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `govern-use-case-seeds` | tool | `tool/source-record-governance-router` | - |
| 2 | `export-entity-ref-rows` | tool | `tool/use-case-seed-entity-ref-exporter` | - |
| 3 | `preflight-entity-relationships` | tool | `tool/factory-jsonl-relationship-preflight` | - |
| 4 | `prepare-bulk-copy` | tool | `tool/factory-jsonl-bulk-copy-loader` | - |

