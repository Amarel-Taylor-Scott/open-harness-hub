# Transfer pricing review (OECD TPG / BEPS / §482 / Pillar Two)

*pipeline* · `pipeline/transfer-pricing-review` · v0.1.0 · experimental

Vertical 21.

| axis | value |
|---|---|
| industry | tax, tax.transfer_pricing, finance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review intercompany transactions for arm's-length compliance + Pillar Two ETR exposure.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-transfer-pricing-flags` | — |
| 4 | `rag_against_oecd` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

