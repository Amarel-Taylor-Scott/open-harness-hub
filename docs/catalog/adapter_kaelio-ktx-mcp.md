# Kaelio ktx MCP tools (propose-only, Baltor disposes)

*adapter* · `adapter/kaelio-ktx-mcp` · v0.1.0 · experimental

Wraps the 11 ktx MCP tools (discover_data, sl_query, wiki_search,
dictionary_search, sql_execution, memory_ingest, …) behind a Baltor
verification gate: ktx PROPOSES (search results, compiled semantic SQL,
query rows + compile-only correctness notes), Baltor DISPOSES (verifies,
receipts, publishes). `sl_query include:["sql","plan"]` supplies the
material our receipts record. Read-only DB connections by upstream
construction.
WRAP CANDIDATE (discovery ≠ trust): admitted from the 2026-06 YC/tool
landscape research as a governed CANDIDATE behind a port — its output is
never served as truth, it is sandboxed, and measured lift is PENDING
(two-axis gate: lift AND structural durability) before any promotion.
Landscape record: docs/strategy/yc-context-landscape-2026-06.md.

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | retrieval, tool_use, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



