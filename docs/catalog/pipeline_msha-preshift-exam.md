# MSHA pre-shift exam GO/NO-GO gate

*pipeline* · `pipeline/msha-preshift-exam` · v0.1.0 · experimental

Apply 30 CFR 75.360 pre-shift exam as a deterministic GO/NO-GO gate — methane / O2 / ventilation / roof-rib-face hazards block miner entry.

| axis | value |
|---|---|
| industry | mining, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply MSHA pre-shift / on-shift exam GO/NO-GO gate.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

