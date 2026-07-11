---
name: climate-disclosure-review
description: Given a corporate climate disclosure (10-K climate section, CDP response,
  sustainability report excerpt), grade against the rubric + cite TCFD recommendation
  / ISSB paragraph / ESRS standard for each finding.
when_to_use: 'Pipeline kind: grading.'
---

# Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)

Grade a corporate climate disclosure against the rubric.
Sixth vertical proving the architecture's industry-agnosticism.
Same 6-step chain: prose → PII redact → GREP → RAG → judge → audit.

## Task

Given a corporate climate disclosure (10-K climate section, CDP
response, sustainability report excerpt), grade against the
rubric + cite TCFD recommendation / ISSB paragraph / ESRS
standard for each finding.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_climate_gaps** — `rule_pack` → `rule-pack/grep-climate-disclosure-gaps`
4. **rag_against_frameworks** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/climate-risk-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-climate-disclosure-gaps`
- **knowledge_packs**: `knowledge-pack/climate-disclosure-frameworks`

## Success criteria

- rubric `rubric/climate-disclosure-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/climate-disclosure-review` v0.1.0
- License: `MIT`
- Industry: climate, esg, finance, compliance
- Full source manifest: see `references/manifest.yaml`
