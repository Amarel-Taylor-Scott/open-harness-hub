# Supplier forced-labour pre-screen (UFLPA / WRO / high-risk-sector triage gate)

*pipeline* · `pipeline/supplier-forced-labor-prescreen` · v0.1.0 · experimental

CHEAP STAGE-1 triage gate for modern-slavery supplier screening. Given a
minimal supplier identity (name, country, product, parent), it decides —
before any expensive deep-tier audit — whether the supplier should be
routed to full forced-labour due diligence, based on keyword/exact-id hits
against UFLPA Entity-List / CBP Withhold-Release-Order signals, the UFLPA
high-priority sectors (cotton, polysilicon, tomatoes), and ILO/UNODC
high-risk-sector + high-risk-corridor markers in the regulatory pack.

Negative-space task: a procurement team onboarding thousands of suppliers
cannot run a full audit on every one, and a bare model asked "is this
supplier risky?" invents a plausible-sounding risk score with no traceable
basis. The durable lift is a *cheap, deterministic, cited* screen that
separates "no signal -> standard onboarding" from "signal -> escalate to
full audit", so the expensive Stage-2 pipeline
(`pipeline/apparel-forced-labor-trace-review`) only runs where a real
signal exists. This is the "screen before you collect" half of the
capability-gap framework applied to supplier intake.

Bundle: Cheap keyword-first (taxonomy Bundle C) — exact-id / keyword
retrieval against the due-diligence pack as the cost floor, a cost-ceiling
gate so the screen stays cheap, and a corrective route: any sanctions/WRO
hit OR a high-risk sector+corridor co-occurrence escalates to the full
audit; otherwise the supplier passes with a cited "no-signal" rationale.
This pipeline makes NO forced-labour determination — it only routes.

| axis | value |
|---|---|
| industry | supply_chain.due_diligence, esg.modern_slavery, procurement.vendor_risk, compliance |
| capability | classification, routing, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Pre-screen a supplier (name, country, product, parent) for forced-labour risk signals and route it: standard-onboarding (no signal) | escalate-to-full-audit (signal found), citing the matched signal.

**pipeline_kind:** `route`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `canonicalize_name` | processor | `processor/name-canonicalize` | - |
| 3 | `normalize_country` | processor | `processor/iso-country-normalize` | - |
| 4 | `cost_gate` | processor | `processor/cost-ceiling-gate` | - |
| 5 | `sanctions_wro_screen` | rule_pack | `rule-pack/sanctions-screening` | - |
| 6 | `grep_sector_corridor` | rule_pack | `rule-pack/grep-apparel-forced-labor-trace-flags` | - |
| 7 | `retrieve_risk_basis` | rule_pack | `rule-pack/grep-apparel-forced-labor-trace-flags` | - |
| 8 | `entity_link` | processor | `processor/entity-resolution-link` | - |
| 9 | `classify_route` | processor | `processor/policy-exception-classifier` | - |
| 10 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 11 | `escalate_if_signal` | processor | `processor/escalate-human-review` | - |
| 12 | `summary` | processor | `processor/review-summary-composer` | - |
| 13 | `audit` | processor | `processor/audit-trace-emitter` | - |

