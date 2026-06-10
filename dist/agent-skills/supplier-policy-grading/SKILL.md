---
name: supplier-policy-grading
description: Given a supplier disclosure pack (policy text, self-assessment, grievance
  summary, optional audit reports), produce a per-section grading against the ESG
  supplier compliance rubric, with citations to ILO indicators / CSDDD articles /
  lead-company code of conduct.
when_to_use: 'Pipeline kind: grading.'
---

# Supplier policy & disclosure grading (CSDDD-aligned)

End-to-end pipeline for grading supplier-submitted policy texts and
self-assessments against the EU CSDDD, ILO forced-labor indicators,
and the lead company's code of conduct. The compliance team submits
a supplier disclosure pack (policy PDF + self-assessment +
grievance summary); the pipeline returns structured findings with
severity, citation, supplier tier, recommended remediation, and
CSDDD-Art.10 right-of-reply path.

Inspired by reviewer feedback on the DueCare ecosystem that
identified ESG / supply-chain due diligence as a natural extension
of the "harness-is-the-lift" architecture.

## Task

Given a supplier disclosure pack (policy text, self-assessment,
grievance summary, optional audit reports), produce a per-section
grading against the ESG supplier compliance rubric, with citations
to ILO indicators / CSDDD articles / lead-company code of conduct.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_social_red_flags** — `rule_pack` → `rule-pack/grep-esg-forced-labor-red-flags`
4. **grep_environmental_red_flags** — `rule_pack` → `rule-pack/grep-esg-environmental-red-flags`
5. **grep_governance_red_flags** — `rule_pack` → `rule-pack/grep-esg-governance-red-flags`
6. **rag_against_global_pack** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
7. **rag_against_corridors** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
8. **rag_against_lead_code** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
9. **grade** — `processor` → `processor/llm-judge`
10. **propose_remediation** — `harness` → `harness/text-safety-review`
11. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/esg-auditor
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-esg-forced-labor-red-flags`, `rule-pack/grep-esg-environmental-red-flags`, `rule-pack/grep-esg-governance-red-flags`, `rule-pack/privacy-pii-text-en`

## Success criteria

- rubric `rubric/esg-supplier-compliance-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/supplier-policy-grading` v0.1.0
- License: `MIT`
- Industry: esg, supply_chain, compliance
- Full source manifest: see `references/manifest.yaml`
