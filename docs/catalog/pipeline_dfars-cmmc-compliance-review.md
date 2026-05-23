# DoD DFARS / CMMC compliance review

*pipeline* · `pipeline/dfars-cmmc-compliance-review` · v0.1.0 · experimental

Vertical 22 — defense acquisition compliance.

| axis | value |
|---|---|
| industry | defense, defense.dfars, defense.cmmc, defense.counterfeit_parts, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review defense supplier packet for DFARS / CMMC / Section 889 / counterfeit-parts compliance.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-defense-dfars-flags` | — |
| 4 | `rag_against_dfars` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

