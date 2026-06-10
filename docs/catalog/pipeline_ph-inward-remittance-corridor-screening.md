# PH inward remittance corridor + counterparty-bank screening

*pipeline* · `pipeline/ph-inward-remittance-corridor-screening` · v0.1.0 · experimental

Screen an inbound cross-border remittance into a Philippine account
(e.g. an OFW remittance corridor) for three risks at once: (1) the
ordering / intermediary BANK is identifiable and valid via its SWIFT
BIC, (2) the originating corridor / jurisdiction is high-risk, and
(3) the remittance pattern matches a structuring / rapid-pass-through
typology — producing a cited risk disposition.

Negative space: a bare model cannot validate a SWIFT BIC or resolve it
to a bank + country, cannot say which corridors are high-risk for PH
inbound flows, and cannot score a deposit series against a structuring
threshold — these are a deterministic BIC validator, a governed
corridor corpus, and a deterministic typology classifier respectively.
The model only assembles the cited disposition. Structuring across a
series of sub-threshold deposits is the canonical pattern a single-
transaction view (and a base model) misses.

Reference / educational only — synthetic remittance inputs, governed
corridor snapshots; not a payment-blocking system. Bundle: Standard
hybrid RAG + deterministic tool legs (BIC, typology) feeding one
governed model call.

| axis | value |
|---|---|
| industry | finance, finance.aml, payments.wires |
| capability | verification, classification, retrieval, safety_gating |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



## Task

Given an inbound PH remittance (amount, ordering bank BIC, origin
country, recent deposit history), validate the counterparty bank via
BIC, assess corridor risk, score the deposit series for structuring /
rapid pass-through, and emit a cited risk disposition. Halt to
escalation on a sanctions hit or a high-severity structuring match.

**pipeline_kind:** `classify`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_pii` | harness | `harness/redact-pii-text` | - |
| 2 | `normalize_origin` | processor | `processor/iso-country-normalize` | - |
| 3 | `validate_bic` | tool | `tool/swift-bic-validator` | - |
| 4 | `canonicalize_beneficiary` | processor | `processor/name-canonicalize` | - |
| 5 | `sanctions_screen` | tool | `tool/sanctions-check` | - |
| 6 | `retrieve_corridor` | knowledge_pack | `knowledge-pack/high-risk-corridors-and-sectors` | - |
| 7 | `structuring_score` | rule_pack | `rule-pack/aml-typologies-fatf` | - |
| 8 | `retrieve_redflags` | knowledge_pack | `knowledge-pack/aml-red-flags-extended` | - |
| 9 | `assemble_disposition` | harness | `harness/aml-investigation` | - |
| 10 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 11 | `escalate` | processor | `processor/escalate-human-review` | $.steps.sanctions_screen.output.matches != [] || $.steps.structuring_score.output.max_severity == 'high' |
| 12 | `audit` | processor | `processor/audit-trace-emitter` | - |

