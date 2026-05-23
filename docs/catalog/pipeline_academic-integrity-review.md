# Academic integrity review (plagiarism / AI / citation fabrication)

*pipeline* · `pipeline/academic-integrity-review` · v0.1.0 · experimental

Ninth vertical. Same chain — only persona / GREP / KB / rubric
change.

| axis | value |
|---|---|
| industry | education, education.higher, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a student submission for plagiarism / AI / fabricated-citation indicators.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_integrity_flags` | rule_pack | `rule-pack/grep-academic-integrity-flags` | — |
| 4 | `rag_against_honor_codes` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

