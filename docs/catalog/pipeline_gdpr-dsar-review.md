# GDPR DSAR fulfillment review (CCPA-compatible)

*pipeline* · `pipeline/gdpr-dsar-review` · v0.1.0 · experimental

Eleventh vertical.

| axis | value |
|---|---|
| industry | privacy, privacy.gdpr, privacy.dsar, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a DSAR fulfillment for completeness + GDPR/CCPA compliance.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-gdpr-dsar-red-flags` | — |
| 4 | `rag_against_gdpr` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

