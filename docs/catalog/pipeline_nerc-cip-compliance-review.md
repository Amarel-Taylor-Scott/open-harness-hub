# NERC CIP compliance review (Bulk Electric System cyber)

*pipeline* · `pipeline/nerc-cip-compliance-review` · v0.1.0 · experimental

Vertical 19.

| axis | value |
|---|---|
| industry | energy, energy.grid, security |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review BES cyber assets + ESP/PSP + access management against NERC CIP.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-nerc-cip-flags` | — |
| 4 | `rag_against_cip` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

