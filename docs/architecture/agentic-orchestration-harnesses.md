# Agentic Orchestration Harnesses

Open Harness Hub should catalog the orchestration layer separately from the
agent. Long-running Codex, Claude Code, or other coding-agent work is less
about a single prompt and more about durable goal state, restart behavior,
budget controls, worktree isolation, progress evidence, and completion audits.

## Harness Families

The core families are:

- persistent goal runtime: a first-class goal object survives compaction,
  terminal closure, and ordinary conversation turns;
- loop continuity: a simple re-read prompt loop updates `STATE.md`, `TODO.md`,
  and logs between runs;
- campaign orchestrator: a daemon or control plane schedules workers, isolates
  worktrees, stores memory, retries failed jobs, and records audit logs;
- backend harness API: a service receives a goal, environment capability set,
  and verification policy, then returns a traceable outcome;
- meta-harness evolver: a harness that proposes, evaluates, and safely updates
  other harnesses using git isolation and benchmark traces;
- workflow wrapper: a scheduler, queue, or visual workflow tool surrounds the
  coding agent with notifications, approvals, and downstream triggers.

## Required Controls

Every long-running harness should specify:

- durable state location;
- restart and compaction policy;
- spending and token guardrails;
- sandbox and permission model;
- worktree or branch isolation;
- progress evidence format;
- completion audit requirements;
- blocked-state criteria;
- human interruption and approval path.

## Catalog Boundary

The static manifest describes the reusable harness pattern. Generated rows in
Postgres should hold individual observed tools, repos, versions, claims, run
traces, pricing snapshots, ratings, and benchmark outcomes.

The distinction matters: the repository can hold a small number of high-quality
orchestration harness manifests while the database stores thousands or millions
of concrete observations about orchestrators, plugins, campaigns, and runs.

## Evaluation Questions

When deciding whether an orchestration harness is useful, ask:

- Can it resume without relying on fragile chat history?
- Can it prove what changed and why?
- Can it bound spend, permissions, and wall-clock runtime?
- Can it split work across isolated agents without file conflicts?
- Can it identify loops or stale progress?
- Can it produce components that a reviewer can validate?
- Can it improve the primitive database rather than only finish one task?
