# PSM Pre-Startup Safety Review (PSSR) gate

*pipeline* · `pipeline/pssr-startup-gate` · v0.1.0 · experimental

Apply 29 CFR 1910.119(i) PSSR as a deterministic gate before unit start-up after maintenance — open Cat-A items / unresolved PHA / training gaps block hydrocarbon introduction.

| axis | value |
|---|---|
| industry | energy, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply PSM Pre-Startup Safety Review GO/NO-GO gate.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

