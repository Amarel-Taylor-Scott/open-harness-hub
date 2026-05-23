# Government benefits adjudication review (SNAP / Medicaid / UI / SSI)

*pipeline* · `pipeline/benefits-adjudication-review` · v0.1.0 · experimental

Tenth vertical. Same 6-step chain — persona / GREP / KB / rubric
swap for benefits-eligibility adjudication.

| axis | value |
|---|---|
| industry | government, government.benefits, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a benefits application + supporting docs; determine eligibility + benefit amount + missing-docs + appeal-rights.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-benefits-eligibility-flags` | — |
| 4 | `rag_against_rules` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

