# ESI 5-Level Triage gate (ER)

*pipeline* · `pipeline/esi-triage-gate` · v0.1.0 · experimental

Apply AHRQ ESI v4 triage algorithm — danger-zone vitals at ESI 3 require upgrade to ESI 2.

| axis | value |
|---|---|
| industry | healthcare, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply ESI triage gate at ED registration.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

