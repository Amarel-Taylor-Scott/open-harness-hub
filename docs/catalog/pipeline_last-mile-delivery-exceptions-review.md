# Last Mile Delivery Exceptions review pipeline

*pipeline* · `pipeline/last-mile-delivery-exceptions-review` · v0.1.0 · experimental

End-to-end last mile delivery exceptions review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | logistics.last_mile, retail.support |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review delivery exceptions for proof-of-delivery quality, refund risk, carrier performance, and customer fairness.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-last-mile-delivery-exceptions-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-last-mile-delivery-exceptions-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/last-mile-delivery-exceptions-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

