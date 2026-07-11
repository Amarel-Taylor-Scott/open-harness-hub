---
name: privacy-dpia-transfer-review
description: Review DPIA and cross-border transfer packets for lawful basis, transfer
  mechanism, residual risk, and data minimization gaps.
when_to_use: 'Pipeline kind: review.'
---

# Privacy DPIA Transfer review pipeline

End-to-end privacy dpia transfer review with redaction, grep triage, RAG grounding, rubric scoring, and audit trace output.

## Task

Review DPIA and cross-border transfer packets for lawful basis, transfer mechanism, residual risk, and data minimization gaps.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_flags** — `rule_pack` → `rule-pack/grep-privacy-dpia-transfer-flags`
4. **retrieve_context** — `rule_pack` → `rule-pack/rag-privacy-dpia-transfer-retrieval-policy`
5. **review_harness** — `harness` → `harness/privacy-dpia-transfer-review`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/privacy-transfer-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/privacy-dpia-transfer-frameworks`
- **rule_packs**: `rule-pack/grep-privacy-dpia-transfer-flags`, `rule-pack/rag-privacy-dpia-transfer-retrieval-policy`

## Success criteria

- rubric `rubric/privacy-dpia-transfer-quality-v1` threshold 0.65

## Provenance

- Hub component: `pipeline/privacy-dpia-transfer-review` v0.1.0
- License: `MIT`
- Industry: privacy, privacy.pia, privacy.gdpr
- Full source manifest: see `references/manifest.yaml`
