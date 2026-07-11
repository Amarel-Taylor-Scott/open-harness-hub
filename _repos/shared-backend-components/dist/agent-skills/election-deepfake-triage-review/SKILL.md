---
name: election-deepfake-triage-review
description: Review election-related media for synthetic manipulation signals, provenance,
  distribution risk, and escalation needs.
when_to_use: 'Pipeline kind: review.'
---

# Election Deepfake Triage review pipeline

Benchmarkable election deepfake triage review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

## Task

Review election-related media for synthetic manipulation signals, provenance, distribution risk, and escalation needs.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-election-deepfake-triage-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-election-deepfake-triage-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/election-deepfake-triage-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **risk_register** — `processor` → `processor/risk-register-updater`
16. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/election-deepfake-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/election-deepfake-triage-frameworks`
- **rule_packs**: `rule-pack/grep-election-deepfake-triage-flags`, `rule-pack/rag-election-deepfake-triage-retrieval-policy`

## Success criteria

- rubric `rubric/election-deepfake-triage-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/election-deepfake-triage-review` v0.1.0
- License: `MIT`
- Industry: election_integrity.deepfake, media.factcheck
- Full source manifest: see `references/manifest.yaml`
