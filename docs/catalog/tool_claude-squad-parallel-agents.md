# Claude Squad parallel-agent harness

*tool* · `tool/claude-squad-parallel-agents` · v0.1.0 · experimental

Launch and coordinate multiple Claude Code agents in parallel using Git
worktrees so each agent has an isolated working tree and can operate on a
different branch or task simultaneously without conflicting. A CLI-driven
harness that spawns N tmux-backed agent sessions, monitors their state, and
merges or reviews outcomes. Suited for fan-out code tasks: parallel
refactors, multi-file feature generation, independent test authoring, or
running this very Open Harness Hub breadth-factory batch.

Reference/integration contract only; verify the upstream license before
bundling.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | agent_loop, planning, tool_use, routing |
| modality | code, text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



