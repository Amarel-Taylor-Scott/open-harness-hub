# Manufacturing NC CAPA review pipeline

*pipeline* · `pipeline/manufacturing-nc-capa-review` · v0.1.0 · experimental

End-to-end manufacturing nc capa review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | manufacturing, manufacturing.qa |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review manufacturing nonconformance and CAPA packets for containment, root cause, corrective action, and verification evidence.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-manufacturing-nc-capa-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-manufacturing-nc-capa-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/manufacturing-nc-capa-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

