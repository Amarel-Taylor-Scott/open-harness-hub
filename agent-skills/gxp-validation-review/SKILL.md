---
name: gxp-validation-review
description: Given a GxP system validation packet (system description + IQ/OQ/PQ outputs
  + audit-trail samples + user-access reviews + change- control history), grade against
  the rubric + cite the relevant regulation section for each finding.
when_to_use: 'Pipeline kind: grading.'
---

# GxP validation review (21-CFR-11 + Annex 11 + ALCOA+)

Review a GxP-validated electronic-records system against the
rubric. Same 6-step chain as ESG / radiology / legal / AppSec —
fifth vertical proving the architecture's industry-agnosticism.

## Task

Given a GxP system validation packet (system description + IQ/OQ/PQ
outputs + audit-trail samples + user-access reviews + change-
control history), grade against the rubric + cite the relevant
regulation section for each finding.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_phi** — `processor` → `processor/redact-pii-text`
3. **grep_phi** — `rule_pack` → `rule-pack/phi-hipaa-en`
4. **grep_gxp_red_flags** — `rule_pack` → `rule-pack/grep-gxp-data-integrity-red-flags`
5. **rag_against_cfr_11** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
6. **grade** — `processor` → `processor/llm-judge`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/gxp-auditor
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/phi-hipaa-en`, `rule-pack/grep-gxp-data-integrity-red-flags`
- **knowledge_packs**: `knowledge-pack/gxp-21-cfr-11-guidelines`

## Success criteria

- rubric `rubric/gxp-validation-quality-v1` threshold 0.7
- deterministic `$.steps.grep_gxp_red_flags.output.hit_count` <= `5`

## Provenance

- Hub component: `pipeline/gxp-validation-review` v0.1.0
- License: `MIT`
- Industry: pharma, pharma.gxp, compliance
- Full source manifest: see `references/manifest.yaml`
