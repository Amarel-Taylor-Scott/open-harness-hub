---
name: datacenter-change-risk-review
description: Review data-center change packets for redundancy, maintenance window,
  rollback, monitoring, and customer impact.
when_to_use: 'Pipeline kind: review.'
---

# Datacenter Change Risk review pipeline

Expanded datacenter change risk review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review data-center change packets for redundancy, maintenance window, rollback, monitoring, and customer impact.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-datacenter-change-risk-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-datacenter-change-risk-retrieval-policy`
6. **review_harness** — `harness` → `harness/datacenter-change-risk-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/datacenter-change-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/datacenter-change-risk-frameworks`
- **rule_packs**: `rule-pack/grep-datacenter-change-risk-flags`, `rule-pack/rag-datacenter-change-risk-retrieval-policy`

## Success criteria

- rubric `rubric/datacenter-change-risk-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/datacenter-change-risk-review` v0.1.0
- License: `MIT`
- Industry: it.datacenter, sre.oncall
- Full source manifest: see `references/manifest.yaml`
