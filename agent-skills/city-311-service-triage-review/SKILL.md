---
name: city-311-service-triage-review
description: Review municipal 311 service packets for priority, duplicate reports,
  safety risk, routing, and closure evidence.
when_to_use: 'Pipeline kind: review.'
---

# City 311 Service Triage review pipeline

Benchmarkable city 311 service triage review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review municipal 311 service packets for priority, duplicate reports, safety risk, routing, and closure evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-city-311-service-triage-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-city-311-service-triage-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/city-311-service-triage-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/city-service-triage-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/city-311-service-triage-frameworks`
- **rule_packs**: `rule-pack/grep-city-311-service-triage-flags`, `rule-pack/rag-city-311-service-triage-retrieval-policy`

## Success criteria

- rubric `rubric/city-311-service-triage-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/city-311-service-triage-review` v0.1.0
- License: `MIT`
- Industry: government.benefits, facilities.maintenance
- Full source manifest: see `references/manifest.yaml`
