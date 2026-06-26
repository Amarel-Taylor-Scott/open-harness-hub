---
name: model-eval-regression-review
description: Review model evaluation runs for regression, benchmark leakage, metric
  drift, and release gating.
when_to_use: 'Pipeline kind: review.'
---

# Model Eval Regression review pipeline

Expanded model eval regression review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

## Task

Review model evaluation runs for regression, benchmark leakage, metric drift, and release gating.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_evidence** — `processor` → `processor/packet-evidence-normalizer`
4. **grep_flags** — `rule_pack` → `rule-pack/grep-model-eval-regression-flags`
5. **retrieve_context** — `rule_pack` → `rule-pack/rag-model-eval-regression-retrieval-policy`
6. **review_harness** — `harness` → `harness/model-eval-regression-review`
7. **dedupe_findings** — `processor` → `processor/finding-deduplicator`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
10. **grade** — `processor` → `processor/llm-judge`
11. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
12. **risk_register** — `processor` → `processor/risk-register-updater`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/model-eval-reviewer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/model-eval-regression-frameworks`
- **rule_packs**: `rule-pack/grep-model-eval-regression-flags`, `rule-pack/rag-model-eval-regression-retrieval-policy`

## Success criteria

- rubric `rubric/model-eval-regression-quality-v1` threshold 0.68
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/model-eval-regression-review` v0.1.0
- License: `MIT`
- Industry: ai, ai_governance
- Full source manifest: see `references/manifest.yaml`
