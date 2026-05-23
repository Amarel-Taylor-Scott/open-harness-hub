# Food safety review (FDA FSMA + HACCP + GFSI)

*pipeline* · `pipeline/food-safety-review` · v0.1.0 · experimental

Seventeenth vertical.

| axis | value |
|---|---|
| industry | food_safety, food_safety.fsma, food_safety.haccp |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a food-safety facility's HACCP plan + supplier verification + traceability.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-food-safety-flags` | — |
| 4 | `rag_against_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

