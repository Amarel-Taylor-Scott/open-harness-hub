# Insurance claim review (NAIC fraud-aware)

*pipeline* · `pipeline/insurance-claim-review` · v0.1.0 · experimental

Eighth vertical proving the architecture's industry-agnosticism.
Same 6-step chain — only persona/rule-pack/knowledge-pack/rubric
change.

| axis | value |
|---|---|
| industry | insurance, insurance.claims, insurance.fraud, finance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Grade an insurance claim submission against the rubric + surface fraud indicators.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_indicators` | rule_pack | `rule-pack/grep-insurance-fraud-red-flags` | — |
| 4 | `rag_against_typologies` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

