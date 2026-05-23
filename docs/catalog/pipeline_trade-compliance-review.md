# Trade compliance review (HTS / EAR / ITAR / OFAC)

*pipeline* · `pipeline/trade-compliance-review` · v0.1.0 · experimental

Thirteenth vertical.

| axis | value |
|---|---|
| industry | trade, trade.eccn, trade.itar, trade.sanctions, compliance |
| capability | evaluation, extraction, verification, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review an export transaction for HTS / ECCN / ITAR classification + destination + end-user + end-use compliance.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-trade-compliance-flags` | — |
| 4 | `rag_against_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

