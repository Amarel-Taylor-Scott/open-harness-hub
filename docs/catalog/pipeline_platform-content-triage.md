# Platform content triage (Trust + Safety)

*pipeline* · `pipeline/platform-content-triage` · v0.1.0 · experimental

Review user-generated content against a documented platform policy. Detects illicit + harmful patterns, routes CSAM suspicion to the human queue + NCMEC referral packet without model classification, generates DSA Art 17 statement of reasons for every restriction.

| axis | value |
|---|---|
| industry | compliance, media, privacy |
| capability | safety_gating, classification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Triage a piece of user-generated content into allow / restrict / remove / escalate.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_triage` | rule_pack | `rule-pack/grep-platform-moderation-flags` | - |
| 4 | `rag_policy` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 5 | `judge` | processor | `processor/llm-judge` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

