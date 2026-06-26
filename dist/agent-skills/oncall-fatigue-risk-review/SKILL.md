---
name: oncall-fatigue-risk-review
description: Review on-call schedules for alert load, sleep disruption, handoff, escalation,
  and burnout risk.
when_to_use: 'Pipeline kind: review.'
---

# On-call Fatigue Risk review pipeline

Benchmarkable on-call fatigue risk review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review on-call schedules for alert load, sleep disruption, handoff, escalation, and burnout risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-oncall-fatigue-risk-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-oncall-fatigue-risk-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/oncall-fatigue-risk-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/oncall-fatigue-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/oncall-fatigue-risk-frameworks`
- **rule_packs**: `rule-pack/grep-oncall-fatigue-risk-flags`, `rule-pack/rag-oncall-fatigue-risk-retrieval-policy`

## Success criteria

- rubric `rubric/oncall-fatigue-risk-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/oncall-fatigue-risk-review` v0.1.0
- License: `MIT`
- Industry: sre.oncall, hr.performance
- Full source manifest: see `references/manifest.yaml`
