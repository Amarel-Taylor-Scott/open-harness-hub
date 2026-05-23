# HR hiring compliance review (EEOC / Title VII / ADA / ADEA)

*pipeline* · `pipeline/hr-hiring-compliance-review` · v0.1.0 · experimental

Twelfth vertical.

| axis | value |
|---|---|
| industry | hr, hr.hiring, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a job posting / screening process for protected-class bias + disparate impact.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_bias_flags` | rule_pack | `rule-pack/grep-hr-hiring-bias-flags` | — |
| 4 | `rag_against_statutes` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

