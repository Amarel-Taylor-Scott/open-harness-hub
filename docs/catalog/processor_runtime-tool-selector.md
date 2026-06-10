# Runtime tool selector (Toolformer / pydantic-ai)

*processor* · `processor/runtime-tool-selector` · v0.1.0 · experimental

Given a user query + a large registry of tools, semantically select
the top-K most likely-relevant tools to expose to the model. Avoids
overflowing the context window with every tool definition when only
a few apply.

Verified by Open Harness Hub clone: implemented at
`pydantic/pydantic-ai/_tool_search.py` (Toolformer-style).

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | routing, retrieval |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



