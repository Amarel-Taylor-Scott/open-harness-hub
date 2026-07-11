# CodeGraph code knowledge-graph query

*tool* · `tool/codegraph-code-graph-query` · v0.1.0 · experimental

Query a pre-indexed code knowledge graph for symbols, their definitions, and
their relationships (callers, callees, imports, references), so an agent can
navigate a large codebase with far fewer tokens and tool calls than reading
files. Integration contract for CodeGraph, a 100%-local code-graph index for
coding agents (Claude Code, Codex, Cursor, OpenCode, Hermes).

This is a reference/integration contract, not a redistribution of upstream
code; verify the upstream license before bundling it. Especially relevant to
this repo: navigating thousands of catalog YAML + factory scripts with low
token cost (pairs with pattern/input-token-compression).

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | retrieval, code_synthesis |
| modality | code, text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



