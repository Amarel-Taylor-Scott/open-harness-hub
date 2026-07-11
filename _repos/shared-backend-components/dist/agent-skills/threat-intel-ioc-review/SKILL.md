---
name: threat-intel-ioc-review
description: Given a CTI report (text + sandbox output), extract IOCs by type, map
  TTPs to ATT&CK techniques, rate confidence, flag attribution concerns.
when_to_use: 'Pipeline kind: review.'
---

# Threat-intel IOC + TTP review (MITRE ATT&CK aligned)

Ingest a CTI report or incident write-up, extract IOCs + TTPs,
validate against MITRE ATT&CK, rate confidence, surface
attribution risk. Seventh vertical proving industry-agnosticism.

## Task

Given a CTI report (text + sandbox output), extract IOCs by type,
map TTPs to ATT&CK techniques, rate confidence, flag attribution
concerns.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_iocs** — `rule_pack` → `rule-pack/grep-ioc-extraction`
4. **rag_against_attack** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
5. **grade** — `processor` → `processor/llm-judge`
6. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/threat-intel-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-ioc-extraction`
- **knowledge_packs**: `knowledge-pack/mitre-attack-sample`

## Success criteria

- rubric `rubric/threat-intel-quality-v1` threshold 0.6

## Provenance

- Hub component: `pipeline/threat-intel-ioc-review` v0.1.0
- License: `MIT`
- Industry: security, threat_intelligence
- Full source manifest: see `references/manifest.yaml`
