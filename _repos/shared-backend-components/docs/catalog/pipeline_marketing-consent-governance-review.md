# Marketing Consent Governance review pipeline

*pipeline* · `pipeline/marketing-consent-governance-review` · v0.1.0 · experimental

End-to-end marketing consent governance review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | marketing_ops.consent, privacy |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review campaign packets for consent basis, preference handling, suppression lists, and unsubscribe controls.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-marketing-consent-governance-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-marketing-consent-governance-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/marketing-consent-governance-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

