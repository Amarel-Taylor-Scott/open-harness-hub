# WHO Surgical Safety Checklist gate (Sign In before induction)

*pipeline* · `pipeline/who-surgical-safety-gate` · v0.1.0 · experimental

Apply the WHO SSC Sign In gate to a pre-induction packet. If any required item is unverified OR any NO-GO is triggered, halt and emit NO-GO.

| axis | value |
|---|---|
| industry | healthcare, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply WHO Surgical Safety Checklist Sign In before induction.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

