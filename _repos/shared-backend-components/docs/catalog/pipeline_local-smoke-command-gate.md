# Local smoke command gate

*pipeline* · `pipeline/local-smoke-command-gate` · v0.1.0 · experimental

Applies local command policies to a generated smoke plan and produces a dry-run execution ledger plus operator approval checklist before any Docker or Postgres commands are run.

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

Gate a generated local smoke plan with command policies and emit a dry-run ledger before local Docker or Postgres execution.

**pipeline_kind:** `research_web.local_smoke_command_gate`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load-local-command-policies` | knowledge_pack | `knowledge-pack/local-smoke-command-policies` | - |
| 2 | `gate-local-smoke-commands` | tool | `tool/local-smoke-command-gate` | - |

