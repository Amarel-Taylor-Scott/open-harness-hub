# Customs entry review (US CBP + UFLPA + USMCA + WCO)

*pipeline* · `pipeline/customs-broker-review` · v0.1.0 · experimental

Vertical 29 — customs-entry compliance: ISF 10+2, HTS classification, FTA origin, UFLPA, AD/CVD.

| axis | value |
|---|---|
| industry | customs, customs.entry, customs.tariff, customs.fta, trade, compliance |
| capability | evaluation, extraction, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review customs entry packet (ISF + HTS + valuation + FTA preference + UFLPA + AD/CVD risk).

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | — |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 3 | `grep_red_flags` | rule_pack | `rule-pack/grep-customs-broker-flags` | — |
| 4 | `rag_against_cbp` | rule_pack | `rule-pack/hybrid-retrieval-policy` | — |
| 5 | `grade` | processor | `processor/llm-judge` | — |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | — |

