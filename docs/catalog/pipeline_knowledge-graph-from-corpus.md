# GraphRAG: knowledge-graph from corpus + global/local query

*pipeline* · `pipeline/knowledge-graph-from-corpus` · v0.1.0 · experimental

Microsoft GraphRAG pattern. Extract entities + relationships from
documents into a graph; build community summaries via Leiden
clustering; query via local (ego-network), global (map-reduce over
communities), or DRIFT (primer + follow-up hybrid).

Verified by Open Harness Hub clone:
`microsoft/graphrag/packages/graphrag/graphrag/query/structured_search/`
contains `local_search/`, `global_search/`, `drift_search/` modules.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | retrieval, reasoning, extraction |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a corpus, build a knowledge graph (entities + relationships +
community summaries); answer queries via local / global / DRIFT search.

**pipeline_kind:** `knowledge_graph`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `extract_entities_and_edges` | harness | `harness/text-safety-review` | — |
| 2 | `build_communities` | processor | `processor/community-summary-mapreduce` | $.inputs.search_mode in ['global', 'drift'] |
| 3 | `local_search` | harness | `harness/text-safety-review` | $.inputs.search_mode == 'local' |
| 4 | `global_search` | harness | `harness/text-safety-review` | $.inputs.search_mode == 'global' |
| 5 | `drift_search` | harness | `harness/text-safety-review` | $.inputs.search_mode == 'drift' |
| 6 | `verify_citations` | processor | `processor/citation-coverage` | — |

