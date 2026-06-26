---
name: patent-prior-art-triage-review
description: Review prior-art search packets for claim mapping, publication dates,
  enablement, jurisdiction, and novelty risk.
when_to_use: 'Pipeline kind: review.'
---

# Patent Prior Art Triage review pipeline

Benchmarkable patent prior art triage review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review prior-art search packets for claim mapping, publication dates, enablement, jurisdiction, and novelty risk.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-patent-prior-art-triage-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-patent-prior-art-triage-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/patent-prior-art-triage-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/prior-art-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/patent-prior-art-triage-frameworks`
- **rule_packs**: `rule-pack/grep-patent-prior-art-triage-flags`, `rule-pack/rag-patent-prior-art-triage-retrieval-policy`

## Success criteria

- rubric `rubric/patent-prior-art-triage-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/patent-prior-art-triage-review` v0.1.0
- License: `MIT`
- Industry: legal.ip, scientific_research.physical
- Full source manifest: see `references/manifest.yaml`
