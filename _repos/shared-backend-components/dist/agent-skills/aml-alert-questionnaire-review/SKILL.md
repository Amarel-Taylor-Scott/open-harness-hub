---
name: aml-alert-questionnaire-review
description: Walk a generated AML alert through an institution-approved question set
  and evidence checklist before close, monitor, EDD, or SAR-style draft routing.
when_to_use: 'Pipeline kind: finance_aml.alert_questionnaire_review.'
---

# AML alert questionnaire review

Review a system-generated AML alert by retrieving procedure knowledge objects, asking required analyst questions, collecting evidence, and producing a cited disposition recommendation.

## Task

Walk a generated AML alert through an institution-approved question set and evidence checklist before close, monitor, EDD, or SAR-style draft routing.

## Steps

1. **redact_alert_text** — `harness` → `harness/redact-pii-text`
2. **retrieve_questions** — `knowledge_pack` → `knowledge-pack/procedure-knowledge-object-patterns`
3. **sanctions_screen** — `tool` → `tool/sanctions-check`
4. **graph_query** — `tool` → `tool/transaction-graph-query`
5. **retrieve_typologies** — `knowledge_pack` → `knowledge-pack/aml-red-flags-extended`
6. **draft_disposition** — `harness` → `harness/aml-investigation`

## Defaults

- **persona**: persona/aml-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/procedure-knowledge-object-patterns`, `knowledge-pack/aml-red-flags-extended`, `knowledge-pack/fatf-typologies-sample`
- **rule_packs**: `rule-pack/financial-pii-en`, `rule-pack/sanctions-screening`, `rule-pack/aml-typologies-fatf`

## Success criteria

- deterministic `$.outputs.answered_questions` is_truthy `True`
- rubric `rubric/aml-investigation-v1` threshold 0.8

## Provenance

- Hub component: `pipeline/aml-alert-questionnaire-review` v0.1.0
- License: `MIT`
- Industry: finance, finance.aml, finance.kyc
- Full source manifest: see `references/manifest.yaml`
