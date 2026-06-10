---
name: suspicious-transaction-review
description: Review a transaction bundle for suspicious activity. Output a sanctions-first
  risk review, FATF typology matches with evidence, and a SAR-style narrative draft
  for BSA officer review.
when_to_use: 'Pipeline kind: classify.'
---

# Suspicious Transaction Review

Given a transaction bundle (account, recent transactions, related
entities), produce a sanctions-first risk review, FATF typology
scoring, and a SAR-style narrative DRAFT (never a SAR filing). PHI
/ financial PII is redacted before any model call; sanctions hits
halt the routine review and route to escalation.

## Task

Review a transaction bundle for suspicious activity. Output a
sanctions-first risk review, FATF typology matches with evidence,
and a SAR-style narrative draft for BSA officer review.

## Steps

1. **redact_pii** — `harness` → `harness/redact-pii-text`
2. **sanctions_screen_entities** — `tool` → `tool/sanctions-check`
3. **graph_query** — `tool` → `tool/transaction-graph-query`
4. **typology_score** — `rule_pack` → `rule-pack/aml-typologies-fatf`
5. **retrieve_fatf** — `knowledge_pack` → `knowledge-pack/fatf-typologies-sample`
6. **investigate** — `harness` → `harness/aml-investigation`

## Defaults

- **persona**: persona/aml-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/fatf-typologies-sample`, `knowledge-pack/sanctions-list-shape`
- **rule_packs**: `rule-pack/financial-pii-en`, `rule-pack/sanctions-screening`, `rule-pack/aml-typologies-fatf`

## Success criteria

- rubric `rubric/aml-investigation-v1` threshold 0.8

## Provenance

- Hub artifact: `pipeline/suspicious-transaction-review` v0.1.0
- License: `MIT`
- Industry: finance, finance.aml
- Full source manifest: see `references/manifest.yaml`
