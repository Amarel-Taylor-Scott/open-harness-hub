# AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

*pipeline* · `pipeline/ai-governance-audit` · v0.1.0 · experimental

Vertical 33 — AI conformity assessment for Annex III high-risk + GPAI + ISO 42001 AIMS.

| axis | value |
|---|---|
| industry | ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001, privacy, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Audit AI system for EU AI Act + NIST + ISO 42001 conformity.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-ai-governance-flags` | — |
| 4 | `rag_against_act` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

