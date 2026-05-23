# KYC/CIP onboarding gate (BSA + USA PATRIOT §326)

*pipeline* · `pipeline/kyc-cip-gate` · v0.1.0 · experimental

Apply CIP 4-element + OFAC + PEP + beneficial-ownership gate before account opening. OFAC hit + cannot-verify-identity = NO-GO.

| axis | value |
|---|---|
| industry | finance, compliance |
| capability | safety_gating, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Apply CIP/CDD gate before account opening.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `checklist_gate` | processor | `processor/checklist-evaluator` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

