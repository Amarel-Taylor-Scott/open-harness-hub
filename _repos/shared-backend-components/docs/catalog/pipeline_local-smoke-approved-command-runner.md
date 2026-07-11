# Local smoke approved command runner

*pipeline* · `pipeline/local-smoke-approved-command-runner` · v0.1.0 · experimental

Turns a gated local smoke command ledger into a plan-only execution ledger, or runs only policy-approved and run-approved commands when explicitly requested.

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

Prepare or execute only policy-approved or run-approved local smoke commands while keeping Docker and Postgres mutation commands blocked unless their command hashes are explicitly approved.

**pipeline_kind:** `research_web.local_smoke_approved_command_runner`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `run-approved-local-smoke-commands` | tool | `tool/local-smoke-approved-command-runner` | - |

