# Document to knowledge graph (nodes + edges with source anchors)

*pipeline* · `pipeline/document-to-knowledge-graph` · v0.1.0 · experimental

Take any source document (contract, SOP, regulatory framework, supply-chain disclosure) and produce a typed knowledge graph with source-anchored nodes + edges. Implements the concept-graph-from-text pattern with three concrete node-type sets: contract-clauses, sop-steps, supply-chain-entities.

| axis | value |
|---|---|
| industry | legal, compliance, supply_chain, research |
| capability | extraction, retrieval |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Extract a typed knowledge graph from a source document.

**pipeline_kind:** `synthesis`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `page_chunk` | processor | `processor/page-aware-chunker` | - |
| 4 | `concept_graph` | processor | `processor/concept-graph-extractor` | - |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | - |

