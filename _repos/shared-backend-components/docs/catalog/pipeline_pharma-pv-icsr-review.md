# Pharma PV ICSR review pipeline

*pipeline* · `pipeline/pharma-pv-icsr-review` · v0.1.0 · experimental

End-to-end pharma pv icsr review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | pharma, pharma.pv, healthcare.pharmacy |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review adverse-event intake packets for ICSR minimum criteria, seriousness, expectedness, causality, and reporting clock risk.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-pharma-pv-icsr-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-pharma-pv-icsr-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/pharma-pv-icsr-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

