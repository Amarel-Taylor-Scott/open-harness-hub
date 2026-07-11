# Claude-Flow swarm orchestrator

*tool* · `tool/claude-flow-swarm-orchestrator` · v0.1.0 · experimental

A large third-party swarm-orchestration framework (ruvnet/claude-flow) that
manages fleets of Claude agents: spawning swarms, routing tasks to
specialists, sharing memory across agents via a distributed state store, and
tracking inter-agent communication. Provides CLI and programmatic interfaces
for launching swarm runs, querying swarm topology, injecting tasks, and
reading aggregated results.

COST AND TRUST CAVEAT: Claude-Flow operates at swarm scale — N concurrent
model calls per run, external state services, and optional cloud hooks.
Budget for significant per-run API spend. Review upstream trust and network
egress requirements before use in sensitive or cost-constrained environments.

Reference/integration contract only; verify the upstream license before
bundling. This is a large, actively-developed third-party project; pin a
release tag for production use.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | agent_loop, planning, routing |
| modality | text, code, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



