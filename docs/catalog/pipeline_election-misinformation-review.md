# Election misinformation / disinformation / synthetic-media review

*pipeline* · `pipeline/election-misinformation-review` · v0.1.0 · experimental

Vertical 23 — election integrity. Same 6-step chain.

| axis | value |
|---|---|
| industry | election_integrity, media, media.factcheck |
| capability | evaluation, extraction, verification |
| modality | text, image |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review election-related content for mis/dis/mal-information + synthetic-media indicators + voter-suppression vectors.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-election-misinformation-flags` | — |
| 4 | `rag_against_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

