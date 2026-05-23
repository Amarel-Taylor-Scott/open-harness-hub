# M&A due-diligence review (6-stream)

*pipeline* · `pipeline/ma-dd-review` · v0.1.0 · experimental

Fifteenth vertical.

| axis | value |
|---|---|
| industry | m_and_a, m_and_a.due_diligence, legal, finance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review M&A target DD packet across 6 streams + propose disposition.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-ma-dd-red-flags` | — |
| 4 | `rag_against_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

