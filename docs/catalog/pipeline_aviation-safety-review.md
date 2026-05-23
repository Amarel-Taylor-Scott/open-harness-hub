# Aviation safety incident review

*pipeline* · `pipeline/aviation-safety-review` · v0.1.0 · experimental

Sixteenth vertical.

| axis | value |
|---|---|
| industry | aviation, aviation.safety |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Classify causation per HFACS + cite NTSB taxonomy + propose corrective actions.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-aviation-safety-flags` | — |
| 4 | `rag_against_frameworks` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

