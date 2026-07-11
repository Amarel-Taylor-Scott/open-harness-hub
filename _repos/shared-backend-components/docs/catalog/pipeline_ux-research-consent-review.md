# UX Research Consent review pipeline

*pipeline* · `pipeline/ux-research-consent-review` · v0.1.0 · experimental

End-to-end ux research consent review with redaction, grep triage, RAG grounding, harness review, rubric scoring, and audit trace.

| axis | value |
|---|---|
| industry | design_ops.research_ethics, privacy |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review UX research plans for consent, participant privacy, incentives, vulnerable populations, and data retention.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-ux-research-consent-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-ux-research-consent-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/ux-research-consent-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

