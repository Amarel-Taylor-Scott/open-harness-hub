# Industry-agnostic pattern: same chain, three verticals

The Open Harness Hub claim is that **a small set of primitives covers
any cite-first, risk-tiered grading task across any industry**. This
doc shows three verticals running on the IDENTICAL pipeline runner
with the SAME 6-step chain - only the persona / rule pack /
knowledge pack / rubric / sample data change.

## The six-step chain

Every grading-style pipeline uses the same shape:

```
[structured input]
     │
     ▼  processor/structured-to-prose
[normalized prose]
     │
     ▼  processor/redact-pii-text   +   rule-pack/{phi|pii}-*-en
[PII/PHI-safe prose]
     │
     ▼  rule-pack/grep-{vertical}-red-flags
[deterministic red-flag hits]
     │
     ▼  rule-pack/hybrid-retrieval-policy → knowledge-pack/{vertical}
[citations from the regulatory / playbook / clinical corpus]
     │
     ▼  processor/llm-judge + rubric/{vertical}-quality-v*
[scored output]
     │
     ▼  processor/audit-trace-emitter
[CSDDD-Art.26 / HIPAA / audit-committee trace]
```

The 6 step-types are **fixed**. The 5 vertical-specific artifacts
swap by industry.

## Three concrete verticals

| Layer | ESG / Supply-chain DD | Healthcare radiology | Legal contract review |
|---|---|---|---|
| Persona | `persona/esg-auditor` | `persona/radiologist-cite-first` | `persona/contract-reviewer-cite-first` |
| GREP rule pack(s) | `grep-esg-forced-labor-red-flags` + `grep-esg-environmental-red-flags` + `grep-esg-governance-red-flags` (3 packs, 39 rules, 13 languages) | `grep-radiology-report-red-flags` (11 rules) | `grep-contract-red-flags` (12 rules) |
| PII / PHI redaction | `rule-pack/privacy-pii-text-en` | `rule-pack/phi-hipaa-en` | `rule-pack/privacy-pii-text-en` |
| RAG knowledge pack | `csddd-and-forced-labor-indicators` (12 jurisdictions + 4 frameworks) + `high-risk-corridors-and-sectors` | `radiology-acrac-fleischner` (ACR AC + Fleischner 2017 + RADS) | `contract-law-clauses` (10 clause families) |
| Rubric | `esg-supplier-compliance-v1` (12-dim, E+S+G) or sub-rubrics | `radiology-report-quality-v1` (8-dim) | `contract-review-quality-v1` (8-dim) |
| Pipeline | `pipeline/supplier-policy-grading` | `pipeline/radiology-report-grading` | `pipeline/contract-clause-review` |
| Sample data | 3 synthetic disclosures (T1 good / T2 mixed / T3 flagged) | 3 synthetic reports (CT-chest-good / CT-abdomen-flagged / mammo-mixed) | 3 synthetic contracts (MSA-clean / NDA-mixed / vendor-flagged) |
| Demo script | `scripts/demo_esg_pipeline.py` | `scripts/demo_radiology_pipeline.py` | `scripts/demo_contract_pipeline.py` |

## Live demo evidence

All three demos run end-to-end against their synthetic samples. The
expected good-supplier / good-report / good-contract sample fires 0
rules; the expected-flagged sample fires multiple critical-tier
rules. **Three industries, one runner, zero false positives on the
clean samples.**

### ESG: `pipeline/supplier-policy-grading`

```
T1 good supplier:     11 steps, 398ms, 0 hits  ✓
T2 Paraguay mixed:    11 steps, 117ms, 2 hits  (E: land-clearing-legacy, near-protected-area)
T3 Mae Sot flagged:   11 steps,  23ms, 10 hits (C:3 H:5 M:2)
                      → passport retention, dorm restriction, recruitment-fee debt,
                        wage deductions, no phones, dye effluent, opaque UBO,
                        audit gap, excessive overtime
```

### Healthcare: `pipeline/radiology-report-grading`

```
CT-chest-good:         7 steps,   4ms, 0 hits  ✓ (Fleischner-compliant)
CT-abdomen-flagged:    7 steps,  39ms, 8 hits  (H:2 M:5 L:1)
                       → missing TI-RADS, missing LI-RADS, missing Fleischner
                         follow-up, no adrenal workup, no Bosniak, definitive
                         metastasis without differential, no comparison,
                         no recommendation
Mammo-mixed:           7 steps,   3ms, 0 hits  ✓ (BIRADS 4B + biopsy recommended)
```

### Legal: `pipeline/contract-clause-review`

```
MSA-clean:             6 steps, 18ms, 0 hits   ✓ (capped indemnity, mutual cap,
                                                  DPA attached, audit rights, etc.)
NDA-mixed:             6 steps,  1ms, 0 hits   ✓ (no critical red flags)
Vendor-flagged:        6 steps,  2ms, 7 hits   (C:3 H:3 M:1)
                       → unlimited liability, asymmetric cap, IP-of-pre-existing,
                         missing anti-bribery, no audit rights, free assignment,
                         narrow force-majeure
```

## What this proves

1. **The architecture is industry-agnostic.** Three verticals share
   100% of the chain shape and 100% of the runner code.
2. **Cross-vertical reuse is real.** `processor/structured-to-prose`,
   `processor/redact-pii-text`, `processor/audit-trace-emitter`,
   `processor/llm-judge`, and `pattern/k-anonymity-aggregation` all
   serve all three verticals.
3. **Adding a new vertical is a 6-artifact PR.** Persona + GREP
   pack(s) + KB + rubric + pipeline + dataset. No runner code, no
   schema changes.
4. **The catalog is more than YAML.** All three demos run with the
   existing `scripts/run_pipeline.py` runner; the deterministic
   steps (4 of 6) produce real output; the model-dependent steps
   (judge / RAG retrieval) cleanly stub until a real adapter is
   plugged in.

## How to add a fourth vertical

Suggested next-vertical candidates and the artifacts each needs:

| Vertical | Persona | GREP rules | Knowledge pack | Rubric |
|---|---|---|---|---|
| AppSec code review | `secrets-scanner` | secret-patterns + CVE-flag + license-noncompat | `owasp-top-10-llm` + `mitre-attack-sample` (both already in catalog) | `code-review-quality-v1` |
| Climate finance | `climate-risk-analyst` | TCFD-noncompliance + transition-plan-gaps | `tcfd-recommendations` + ESRS-E1 (partial in catalog) | `climate-risk-quality-v1` |
| Defense supply integrity | `defense-acquisition-officer` | ITAR-noncompliance + counterfeit-parts + dual-use-leak | `itar-categories` + `defense-counterfeit-incidents` | `defense-acq-quality-v1` |
| Pharma compliance | `gxp-auditor` | data-integrity + 21-CFR-11-noncompliance | `21-cfr-11` + `ich-gxp-guidelines` | `gxp-audit-quality-v1` |
| Education / academic integrity | `academic-integrity-officer` | plagiarism + AI-generated-flags + citation-fabrication | `apa-citation-rules` + `academic-honor-codes` | `academic-integrity-v1` |

Each is a 1-day PR using the same template.
