# NFPA 70E Lockout/Tagout gate

*pipeline* · `pipeline/nfpa-70e-loto-gate` · v0.1.0 · experimental

Apply NFPA 70E + OSHA 1910.147 LOTO gate — voltage detected after isolation = re-isolate.

| axis | value |
|---|---|
| industry | energy, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply LOTO gate before electrical work.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

