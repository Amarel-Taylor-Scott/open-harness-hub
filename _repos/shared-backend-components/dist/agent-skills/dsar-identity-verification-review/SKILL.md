---
name: dsar-identity-verification-review
description: Review DSAR identity packets for requester authorization, fraud risk,
  data scope, deadline, and response limitations.
when_to_use: 'Pipeline kind: review.'
---

# DSAR Identity Verification review pipeline

Benchmarkable dsar identity verification review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review DSAR identity packets for requester authorization, fraud risk, data scope, deadline, and response limitations.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-dsar-identity-verification-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-dsar-identity-verification-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/dsar-identity-verification-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/dsar-identity-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/dsar-identity-verification-frameworks`
- **rule_packs**: `rule-pack/grep-dsar-identity-verification-flags`, `rule-pack/rag-dsar-identity-verification-retrieval-policy`

## Success criteria

- rubric `rubric/dsar-identity-verification-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/dsar-identity-verification-review` v0.1.0
- License: `MIT`
- Industry: privacy.dsar, security.fraud
- Full source manifest: see `references/manifest.yaml`
