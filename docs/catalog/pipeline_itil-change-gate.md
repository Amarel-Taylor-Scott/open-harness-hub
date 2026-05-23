# ITIL Change Enablement gate

*pipeline* · `pipeline/itil-change-gate` · v0.1.0 · experimental

Apply ITIL 4 change-enablement runbook as deterministic gate — CAB approval + backout plan + validation criteria are GO requirements.

| axis | value |
|---|---|
| industry | it, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply ITIL change-enablement gate before production change.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

