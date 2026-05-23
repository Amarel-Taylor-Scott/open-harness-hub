# DOT pre-trip inspection gate (DVIR / 49 CFR 396)

*pipeline* · `pipeline/dot-pretrip-gate` · v0.1.0 · experimental

Apply driver vehicle inspection report gate — out-of-service criteria block dispatch.

| axis | value |
|---|---|
| industry | transportation, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply DVIR gate before truck dispatch.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

