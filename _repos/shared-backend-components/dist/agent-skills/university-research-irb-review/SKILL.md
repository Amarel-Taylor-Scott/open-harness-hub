---
name: university-research-irb-review
description: Review human-subjects research packets for consent, risk, data handling,
  recruitment, and vulnerable populations.
when_to_use: 'Pipeline kind: review.'
---

# University Research IRB review pipeline

Expanded university research irb review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review human-subjects research packets for consent, risk, data handling, recruitment, and vulnerable populations.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-university-research-irb-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-university-research-irb-retrieval-policy`
6. **review_harness** — `harness` → `harness/university-research-irb-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/irb-intake-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/university-research-irb-frameworks`
- **rule_packs**: `rule-pack/grep-university-research-irb-flags`, `rule-pack/rag-university-research-irb-retrieval-policy`

## Success criteria

- rubric `rubric/university-research-irb-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/university-research-irb-review` v0.1.0
- License: `MIT`
- Industry: education.higher, scientific_research.social
- Full source manifest: see `references/manifest.yaml`
