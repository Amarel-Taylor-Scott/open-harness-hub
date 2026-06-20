# Retail Returns Abuse review pipeline

*pipeline* · `pipeline/retail-returns-abuse-review` · v0.1.0 · experimental

End-to-end retail returns abuse review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | retail, retail.support, security.fraud |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review retail return cases for policy compliance, customer fairness, fraud indicators, and escalation needs.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-retail-returns-abuse-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-retail-returns-abuse-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/retail-returns-abuse-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

