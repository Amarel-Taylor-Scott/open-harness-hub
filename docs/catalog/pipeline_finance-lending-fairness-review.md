# Finance Lending Fairness review pipeline

*pipeline* · `pipeline/finance-lending-fairness-review` · v0.1.0 · experimental

End-to-end finance lending fairness review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | finance, finance.lending, compliance |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review lending decision packets for adverse-action reasons, fair-lending proxy risk, documentation sufficiency, and escalation needs.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-finance-lending-fairness-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-finance-lending-fairness-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/finance-lending-fairness-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

