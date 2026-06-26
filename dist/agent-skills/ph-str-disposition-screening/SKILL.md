---
name: ph-str-disposition-screening
description: Given an AML alert, run a sanctions-first gate, score the transaction
  sequence against FATF/AMLA typologies, and recommend a disposition (close / monitor
  / enhanced_due_diligence / str_style_draft / sanctions_escalation) with cited indicators
  and a narrative DRAFT — halting to escalation on any sanctions hit, never filing
  an STR.
when_to_use: 'Pipeline kind: classify.'
---

# PH suspicious-transaction disposition screening (sanctions-first)

Walk a Philippine AML alert (transaction bundle + customer profile +
counterparties) through a sanctions-first gate, then deterministic
FATF/AMLA typology scoring, then a cited disposition recommendation —
close, monitor, enhanced due diligence, STR-style DRAFT, or sanctions
escalation. It NEVER files an STR and never asserts intent; it produces
an analyst-ready, cited recommendation with the matched indicators.

Negative space: a bare model, given an alert, fluently invents a
disposition with no provenance, no sanctions check, and no typology
evidence — exactly the failure that makes "just ask the model"
unsafe for AML. Here the sanctions check is a deterministic tool that
short-circuits to escalation on a hit; the typology evidence is a
deterministic classifier; the model only composes the cited narrative
draft under a cite-or-abstain contract. The sanctions-first ordering
(a hit halts BEFORE any disposition is drafted) is the control a base
model has no notion of.

Reference / educational only — synthetic alerts, governed corpora; a
drafting aid for a BSA/compliance officer, not a filing. Bundle:
Agentic/governed review — sanctions-first Conditional gate + cited
model call + deterministic verify.

## Task

Given an AML alert, run a sanctions-first gate, score the transaction
sequence against FATF/AMLA typologies, and recommend a disposition
(close / monitor / enhanced_due_diligence / str_style_draft /
sanctions_escalation) with cited indicators and a narrative DRAFT —
halting to escalation on any sanctions hit, never filing an STR.

## Steps

1. **redact_pii** — `harness` → `harness/redact-pii-text`
2. **canonicalize_customer** — `processor` → `processor/name-canonicalize`
3. **sanctions_screen** — `tool` → `tool/sanctions-check`
4. **graph_query** — `tool` → `tool/transaction-graph-query`
5. **typology_score** — `rule_pack` → `rule-pack/aml-typologies-fatf`
6. **retrieve_fatf** — `knowledge_pack` → `knowledge-pack/fatf-typologies-sample`
7. **retrieve_redflags** — `knowledge_pack` → `knowledge-pack/aml-red-flags-extended`
8. **draft_disposition** — `harness` → `harness/aml-investigation`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **check_citations** — `processor` → `processor/citation-span-checker`
11. **escalate** — `processor` → `processor/escalate-human-review` (when `$.steps.sanctions_screen.output.matches != []`)
12. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/aml-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/fatf-typologies-sample`, `knowledge-pack/aml-red-flags-extended`, `knowledge-pack/sanctions-list-shape`
- **rule_packs**: `rule-pack/financial-pii-en`, `rule-pack/sanctions-screening`, `rule-pack/aml-typologies-fatf`

## Success criteria

- rubric `rubric/aml-investigation-v1` threshold 0.8
- deterministic `$.steps.check_citations.output.result.pass` == `True`
- regex `(has been filed|will be filed|we have filed|STR filed)` against `$.outputs.analyst_narrative_draft`

## Provenance

- Hub component: `pipeline/ph-str-disposition-screening` v0.1.0
- License: `MIT`
- Industry: finance, finance.aml, finance.kyc
- Full source manifest: see `references/manifest.yaml`
