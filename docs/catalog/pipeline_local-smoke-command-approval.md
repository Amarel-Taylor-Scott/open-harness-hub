# Local smoke command approval

*pipeline* · `pipeline/local-smoke-command-approval` · v0.1.0 · experimental

Creates and verifies run-scoped approval records for command hashes in local smoke command gates before any Docker or Postgres command is eligible for execution.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | governance, evaluation, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Create a run-scoped approval template for a command gate, or verify a completed approval record against command hashes before execution.

**pipeline_kind:** `research_web.local_smoke_command_approval`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `create-local-smoke-command-approval-template` | tool | `tool/local-smoke-command-approval-verifier` | - |

