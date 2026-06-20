---
name: social-platform-appeals-review
description: Review moderation appeals for policy fit, evidence quality, user safety,
  enforcement consistency, and restoration risk.
when_to_use: 'Pipeline kind: review.'
---

# Social Platform Appeals review pipeline

Benchmarkable social platform appeals review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review moderation appeals for policy fit, evidence quality, user safety, enforcement consistency, and restoration risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-social-platform-appeals-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-social-platform-appeals-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/social-platform-appeals-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/platform-appeals-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/social-platform-appeals-frameworks`
- **rule_packs**: `rule-pack/grep-social-platform-appeals-flags`, `rule-pack/rag-social-platform-appeals-retrieval-policy`

## Success criteria

- rubric `rubric/social-platform-appeals-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/social-platform-appeals-review` v0.1.0
- License: `MIT`
- Industry: media.distribution, media.distribution
- Full source manifest: see `references/manifest.yaml`
