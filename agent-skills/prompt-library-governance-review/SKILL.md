---
name: prompt-library-governance-review
description: Review prompt library entries for versioning, owners, eval coverage,
  data handling, and deprecation controls.
when_to_use: 'Pipeline kind: review.'
---

# Prompt Library Governance review pipeline

Benchmarkable prompt library governance review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review prompt library entries for versioning, owners, eval coverage, data handling, and deprecation controls.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-prompt-library-governance-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-prompt-library-governance-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/prompt-library-governance-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/prompt-library-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/prompt-library-governance-frameworks`
- **rule_packs**: `rule-pack/grep-prompt-library-governance-flags`, `rule-pack/rag-prompt-library-governance-retrieval-policy`

## Success criteria

- rubric `rubric/prompt-library-governance-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/prompt-library-governance-review` v0.1.0
- License: `MIT`
- Industry: ai, software.docs
- Full source manifest: see `references/manifest.yaml`
