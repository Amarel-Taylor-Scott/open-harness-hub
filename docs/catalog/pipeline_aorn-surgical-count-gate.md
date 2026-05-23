# AORN Surgical Count GO/NO-GO gate

*pipeline* · `pipeline/aorn-surgical-count-gate` · v0.1.0 · experimental

Apply AORN Sponge/Sharp/Instrument count gate before patient leaves OR — discrepancy requires intra-op imaging.

| axis | value |
|---|---|
| industry | healthcare, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply AORN surgical count gate before OR transport.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

