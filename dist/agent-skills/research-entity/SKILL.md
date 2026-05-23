---
name: research-entity
description: 'Given (entity_name, entity_kind, optional_country), produce a one-page
  sourced profile with: short description, key facts, recent events, conflict-or-controversy
  section, and a citation list. Every claim is cited; PII is redacted before any external
  call.'
when_to_use: 'Pipeline kind: research_entity.'
---

# Research Entity

Given an entity name + entity kind (company / person / place / product),
produce a sourced one-page profile. Verifiable, cited, redacted.

## Task

Given (entity_name, entity_kind, optional_country), produce a one-page
sourced profile with: short description, key facts, recent events,
conflict-or-controversy section, and a citation list. Every claim is
cited; PII is redacted before any external call.

## Steps

1. **redact_query** — `harness` → `harness/redact-pii-text`
2. **plan** — `harness` → `harness/text-safety-review`
3. **search** — `tool` → `tool/web-search`
4. **verify_sources** — `harness` → `harness/text-safety-review`
5. **extract_facts** — `harness` → `harness/text-safety-review`
6. **compose** — `harness` → `harness/text-safety-review`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: —
- **rule_packs**: `rule-pack/privacy-pii-text-en`, `rule-pack/web-search-allowlist-default`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.75

## Provenance

- Hub artifact: `pipeline/research-entity` v0.1.0
- License: `MIT`
- Industry: cross_industry
- Full source manifest: see `references/manifest.yaml`
