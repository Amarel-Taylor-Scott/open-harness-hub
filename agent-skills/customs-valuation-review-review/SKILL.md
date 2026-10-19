---
name: customs-valuation-review-review
description: Review customs valuation packets for assists, royalties, related-party
  pricing, freight, and invoice evidence.
when_to_use: 'Pipeline kind: review.'
---

# Customs Valuation Review review pipeline

Benchmarkable customs valuation review review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review customs valuation packets for assists, royalties, related-party pricing, freight, and invoice evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-customs-valuation-review-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-customs-valuation-review-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/customs-valuation-review-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/customs-valuation-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/customs-valuation-review-frameworks`
- **rule_packs**: `rule-pack/grep-customs-valuation-review-flags`, `rule-pack/rag-customs-valuation-review-retrieval-policy`

## Success criteria

- rubric `rubric/customs-valuation-review-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/customs-valuation-review-review` v0.1.0
- License: `MIT`
- Industry: customs.entry, trade.hts
- Full source manifest: see `references/manifest.yaml`
