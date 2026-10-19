---
name: animal-research-iacuc-review
description: Review animal research protocols for humane endpoints, analgesia, species
  justification, training, and adverse-event reporting.
when_to_use: 'Pipeline kind: review.'
---

# Animal Research IACUC review pipeline

Benchmarkable animal research iacuc review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

## Task

Review animal research protocols for humane endpoints, analgesia, species justification, training, and adverse-event reporting.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-animal-research-iacuc-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-animal-research-iacuc-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/animal-research-iacuc-review`
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

- **persona**: persona/iacuc-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/animal-research-iacuc-frameworks`
- **rule_packs**: `rule-pack/grep-animal-research-iacuc-flags`, `rule-pack/rag-animal-research-iacuc-retrieval-policy`

## Success criteria

- rubric `rubric/animal-research-iacuc-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/animal-research-iacuc-review` v0.1.0
- License: `MIT`
- Industry: research.animal_welfare, scientific_research.bio
- Full source manifest: see `references/manifest.yaml`
