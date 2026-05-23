# FAA Part 91 Before-Takeoff gate

*pipeline* · `pipeline/faa-preflight-gate` · v0.1.0 · experimental

Apply the FAA before-takeoff checklist as a deterministic GO/NO-GO gate.

| axis | value |
|---|---|
| industry | aviation, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply FAA Before-Takeoff Checklist + Takeoff Briefing.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

