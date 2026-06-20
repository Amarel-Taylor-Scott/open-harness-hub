---
name: rail-crew-hours-compliance-review
description: Review rail crew hours packets for rest periods, duty time, deadhead,
  fatigue risk, and exception evidence.
when_to_use: 'Pipeline kind: review.'
---

# Rail Crew Hours Compliance review pipeline

Benchmarkable rail crew hours compliance review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review rail crew hours packets for rest periods, duty time, deadhead, fatigue risk, and exception evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-rail-crew-hours-compliance-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-rail-crew-hours-compliance-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/rail-crew-hours-compliance-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/rail-hours-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/rail-crew-hours-compliance-frameworks`
- **rule_packs**: `rule-pack/grep-rail-crew-hours-compliance-flags`, `rule-pack/rag-rail-crew-hours-compliance-retrieval-policy`

## Success criteria

- rubric `rubric/rail-crew-hours-compliance-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/rail-crew-hours-compliance-review` v0.1.0
- License: `MIT`
- Industry: transportation.rail
- Full source manifest: see `references/manifest.yaml`
