---
name: port-terminal-security-review
description: Review port terminal incidents for access control, cargo integrity, ISPS
  controls, and escalation.
when_to_use: 'Pipeline kind: review.'
---

# Port Terminal Security review pipeline

Expanded port terminal security review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review port terminal incidents for access control, cargo integrity, ISPS controls, and escalation.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-port-terminal-security-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-port-terminal-security-retrieval-policy`
6. **review_harness** — `harness` → `harness/port-terminal-security-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/port-security-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/port-terminal-security-frameworks`
- **rule_packs**: `rule-pack/grep-port-terminal-security-flags`, `rule-pack/rag-port-terminal-security-retrieval-policy`

## Success criteria

- rubric `rubric/port-terminal-security-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/port-terminal-security-review` v0.1.0
- License: `MIT`
- Industry: maritime.port_security, security.defensive
- Full source manifest: see `references/manifest.yaml`
