---
name: home-health-plan-review-review
description: Review home health plans for eligibility, visit frequency, goals, safety,
  and documentation sufficiency.
when_to_use: 'Pipeline kind: review.'
---

# Home Health Plan Review review pipeline

Benchmarkable home health plan review review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review home health plans for eligibility, visit frequency, goals, safety, and documentation sufficiency.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-home-health-plan-review-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-home-health-plan-review-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/home-health-plan-review-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/home-health-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/home-health-plan-review-frameworks`
- **rule_packs**: `rule-pack/grep-home-health-plan-review-flags`, `rule-pack/rag-home-health-plan-review-retrieval-policy`

## Success criteria

- rubric `rubric/home-health-plan-review-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/home-health-plan-review-review` v0.1.0
- License: `MIT`
- Industry: healthcare.clinical, healthcare.payer
- Full source manifest: see `references/manifest.yaml`
