# TRID Loan Estimate + Closing Disclosure gate

*pipeline* · `pipeline/trid-loan-gate` · v0.1.0 · experimental

Apply Reg Z TRID timing + tolerance gate before mortgage consummation — CD timing miss = NO-GO + re-issue.

| axis | value |
|---|---|
| industry | finance, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply TRID gate before mortgage consummation.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

