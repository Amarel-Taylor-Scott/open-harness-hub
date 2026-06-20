# Media Claims Factcheck review pipeline

*pipeline* · `pipeline/media-claims-factcheck-review` · v0.1.0 · experimental

End-to-end media claims factcheck review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

| axis | value |
|---|---|
| industry | media, media.factcheck |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review article claims for source quality, quote fidelity, unsupported assertions, and correction risk.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-media-claims-factcheck-flags` | - |
| 4 | `retrieve_context` | rule_pack | `rule-pack/rag-media-claims-factcheck-retrieval-policy` | - |
| 5 | `review_harness` | harness | `harness/media-claims-factcheck-review` | - |
| 6 | `grade` | processor | `processor/llm-judge` | - |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | - |

