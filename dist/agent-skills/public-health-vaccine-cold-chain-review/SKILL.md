---
name: public-health-vaccine-cold-chain-review
description: Review vaccine cold-chain packets for excursion handling, inventory hold,
  lot tracking, clinic notification, and release evidence.
when_to_use: 'Pipeline kind: review.'
---

# Public Health Vaccine Cold Chain review pipeline

Benchmarkable public health vaccine cold chain review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

## Task

Review vaccine cold-chain packets for excursion handling, inventory hold, lot tracking, clinic notification, and release evidence.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-public-health-vaccine-cold-chain-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-public-health-vaccine-cold-chain-retrieval-policy`
6. **control_matrix** — `processor` → `processor/control-matrix-builder`
7. **review_harness** — `harness` → `harness/public-health-vaccine-cold-chain-review`
8. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
9. **calibrate_severity** — `processor` → `processor/severity-calibrator`
10. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
11. **route_owners** — `processor` → `processor/remediation-owner-router`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`

## Defaults

- **persona**: persona/vaccine-cold-chain-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/public-health-vaccine-cold-chain-frameworks`
- **rule_packs**: `rule-pack/grep-public-health-vaccine-cold-chain-flags`, `rule-pack/rag-public-health-vaccine-cold-chain-retrieval-policy`

## Success criteria

- rubric `rubric/public-health-vaccine-cold-chain-quality-v1` threshold 0.7
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`
- deterministic `$.steps.check_citations.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/public-health-vaccine-cold-chain-review` v0.1.0
- License: `MIT`
- Industry: healthcare.public_health, logistics.cold_chain
- Full source manifest: see `references/manifest.yaml`
