---
name: airport-slot-coordination-review
description: Review airport slot packets for allocation rules, historic precedence,
  misuse, waiver, and operational constraints.
when_to_use: 'Pipeline kind: review.'
---

# Airport Slot Coordination review pipeline

Benchmarkable airport slot coordination review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review airport slot packets for allocation rules, historic precedence, misuse, waiver, and operational constraints.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-airport-slot-coordination-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-airport-slot-coordination-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/airport-slot-coordination-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/slot-coordination-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/airport-slot-coordination-frameworks`
- **rule_packs**: `rule-pack/grep-airport-slot-coordination-flags`, `rule-pack/rag-airport-slot-coordination-retrieval-policy`

## Success criteria

- rubric `rubric/airport-slot-coordination-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/airport-slot-coordination-review` v0.1.0
- License: `MIT`
- Industry: aviation.flight_crew, government.regulatory
- Full source manifest: see `references/manifest.yaml`
