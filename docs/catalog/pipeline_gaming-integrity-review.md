# Gaming integrity review (BSA AML + responsible-gambling + match-fixing)

*pipeline* · `pipeline/gaming-integrity-review` · v0.1.0 · experimental

Vertical 26 — gaming-operator review: AML/CTR/SAR, self-exclusion, source-of-funds, match-fixing.

| axis | value |
|---|---|
| industry | gaming, gaming.aml, gaming.responsible, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review gaming operator compliance packet (CTR/SAR filings + self-exclusion + SOF + match-fixing monitoring).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-gaming-integrity-flags` | — |
| 4 | `rag_against_bsa` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

