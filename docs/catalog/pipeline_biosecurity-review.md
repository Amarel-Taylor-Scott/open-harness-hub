# Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)

*pipeline* · `pipeline/biosecurity-review` · v0.1.0 · experimental

Vertical 32 — registered select-agent entity + BSL-3/4 lab compliance + DURC.

| axis | value |
|---|---|
| industry | biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review select-agent registered entity compliance packet.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-biosecurity-flags` | — |
| 4 | `rag_against_cdc` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

