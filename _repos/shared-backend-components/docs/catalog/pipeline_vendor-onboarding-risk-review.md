# Vendor Onboarding Risk review pipeline

*pipeline* · `pipeline/vendor-onboarding-risk-review` · v0.1.0 · experimental

End-to-end vendor onboarding risk review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | procurement.vendor_risk, compliance |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review vendor onboarding packets for sanctions, security, privacy, financial, insurance, and concentration risk.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-vendor-onboarding-risk-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-vendor-onboarding-risk-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/vendor-onboarding-risk-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

