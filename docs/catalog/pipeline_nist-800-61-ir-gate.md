# NIST 800-61 Incident Response gate

*pipeline* · `pipeline/nist-800-61-ir-gate` · v0.1.0 · experimental

Apply NIST SP 800-61 IR playbook — confirmed data exfil escalates to IC + legal.

| axis | value |
|---|---|
| industry | cyber, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply IR playbook gate at incident declaration.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

