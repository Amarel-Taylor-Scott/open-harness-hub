# Multi-agent swarm orchestration

*pattern* · `pattern/multi-agent-swarm-orchestration` · v0.1.0 · experimental

A lead orchestrator agent decomposes a broad or ambiguous goal into
independent work packages and dispatches them in parallel to a swarm of
specialist subagents — each operating in its own isolated context (git
worktree, process, or MCP session). Subagents produce structured outputs
(YAML manifests, JSONL rows, reports, code patches) that the orchestrator
aggregates, validates, and gates before promotion or merge.

This is the model used to drive Open Harness Hub breadth-factory batches:
a BREADTH agent fans out to N concurrent workers that each catalog or
generate a different component family, then the orchestrator collects and
validates the results. The pattern differs from simple Orchestrator-Workers
in that subagents themselves may invoke tools (search, shell, model calls)
and are expected to self-correct before returning results.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | agent_loop, planning, routing |
| modality | text, code, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



