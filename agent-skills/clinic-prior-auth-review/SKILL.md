---
name: clinic-prior-auth-review
description: Review prior authorization packets for medical necessity evidence, payer
  criteria, denial risk, and appeal gaps.
when_to_use: 'Pipeline kind: review.'
---

# Clinic Prior Authorization review pipeline

Expanded clinic prior authorization review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review prior authorization packets for medical necessity evidence, payer criteria, denial risk, and appeal gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-clinic-prior-auth-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-clinic-prior-auth-retrieval-policy`
6. **review_harness** — `harness` → `harness/clinic-prior-auth-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/prior-auth-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/clinic-prior-auth-frameworks`
- **rule_packs**: `rule-pack/grep-clinic-prior-auth-flags`, `rule-pack/rag-clinic-prior-auth-retrieval-policy`

## Success criteria

- rubric `rubric/clinic-prior-auth-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/clinic-prior-auth-review` v0.1.0
- License: `MIT`
- Industry: healthcare.clinical, healthcare.payer
- Full source manifest: see `references/manifest.yaml`
