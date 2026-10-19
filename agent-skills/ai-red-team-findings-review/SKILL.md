---
name: ai-red-team-findings-review
description: Review AI red-team reports for exploit reproducibility, severity, mitigation,
  policy coverage, and regression tests.
when_to_use: 'Pipeline kind: review.'
---

# AI Red Team Findings review pipeline

Benchmarkable ai red team findings review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review AI red-team reports for exploit reproducibility, severity, mitigation, policy coverage, and regression tests.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-ai-red-team-findings-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-ai-red-team-findings-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/ai-red-team-findings-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/ai-red-team-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/ai-red-team-findings-frameworks`
- **rule_packs**: `rule-pack/grep-ai-red-team-findings-flags`, `rule-pack/rag-ai-red-team-findings-retrieval-policy`

## Success criteria

- rubric `rubric/ai-red-team-findings-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/ai-red-team-findings-review` v0.1.0
- License: `MIT`
- Industry: ai, security.offensive
- Full source manifest: see `references/manifest.yaml`
