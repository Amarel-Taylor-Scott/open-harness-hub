# Privacy DPIA Transfer review pipeline

*pipeline* · `pipeline/privacy-dpia-transfer-review` · v0.1.0 · experimental

End-to-end privacy dpia transfer review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | privacy, privacy.pia, privacy.gdpr |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review DPIA and cross-border transfer packets for lawful basis, transfer mechanism, residual risk, and data minimization gaps.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-privacy-dpia-transfer-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-privacy-dpia-transfer-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/privacy-dpia-transfer-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

