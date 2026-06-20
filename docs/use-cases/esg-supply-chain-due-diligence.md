# Use case: ESG / Supply-Chain Due Diligence (CSDDD + CSRD + 12 jurisdictions)

## What this answers

> "We need to audit our deep-tier supplier networks (tier 3 and tier
> 4+) for forced labor, environmental harm, AND governance gaps -
> across the EU CSDDD, CSRD ESRS E1-E5 / S1-S2, the UK MSA, German
> LkSG, France Loi Vigilance, Norway Åpenhetsloven, Swiss CO Art.
> 964j, California SB 657, US UFLPA + Tariff Act §307, Canada Bill
> S-211, Australia MSA, and Japan METI Guidelines - without hiring
> 100 more ESG analysts. AND we need to share rogue-broker / rogue-
> corridor signals with peer orgs without leaking confidential
> supply-chain data."

## Catalog ingredients (v0.2.0 - full E + S + G coverage)

| Layer | Component | Role |
|---|---|---|
| Persona | `persona/esg-auditor` | Citation-first auditor covering all 12 jurisdictions, ESRS E1-E5 + S1-S2, ILO core conventions, ISO 37001 |
| GREP rule pack (**S**) | `rule-pack/grep-esg-forced-labor-red-flags` | 17 detectors for ILO indicators 1-11 + child labor + recruitment-fee abuse + 12 high-risk corridors + 13-language coverage (en/zh/hi/bn/ko/vi/th/id/tl/es/pt/fr/ar) |
| GREP rule pack (**E**) | `rule-pack/grep-esg-environmental-red-flags` | 14 detectors for deforestation, hazardous waste, water pollution, water-stress sourcing, Scope-3 underreporting, missing transition plans, biodiversity (KBA/protected areas), conflict minerals, ozone-depleting substances |
| GREP rule pack (**G**) | `rule-pack/grep-esg-governance-red-flags` | 12 detectors for UBO opacity, shell-jurisdictions, facilitation payments, third-party-agent gaps, whistleblower retaliation, audit-trail gaps, sanctions / PEP screening |
| RAG knowledge pack (regulatory) | `knowledge-pack/csddd-and-forced-labor-indicators` | 21-source citation backbone: CSDDD + CSRD + EUDR + Conflict Minerals + UK MSA + LkSG + Loi Vigilance + Åpenhetsloven + Swiss 964j + NL CLDD + SB 657 + UFLPA + Tariff Act §307 + Canada S-211 + Australia MSA + Japan METI + UNGPs + OECD MNE + OECD DD + ETI Base Code + CBP WRO snapshot |
| RAG knowledge pack (corridors) | `knowledge-pack/high-risk-corridors-and-sectors` | Geographic + sectoral risk map (apparel/electronics/agri/construction/seafood/brick-kilns/carpets), CBP WRO snapshot, UFLPA Entity List snapshot, ITUC Global Rights Index |
| PII redaction | `rule-pack/privacy-pii-text-en` + `processor/redact-pii-text` | Strips worker grievance transcript PII before LLM call (HIPAA Safe Harbor 18-category) |
| Judge rubric (full) | `rubric/esg-supplier-compliance-v1` | **12-dimension** rubric, explicit E + S + G + cross-cutting groups |
| Judge rubric (E only) | `rubric/esg-env-v1` | 5-dimension ESRS E1-E5 sub-rubric |
| Judge rubric (S only) | `rubric/esg-social-v1` | 6-dimension ILO + ESRS S1-S2 sub-rubric |
| Judge rubric (G only) | `rubric/esg-gov-v1` | 6-dimension OECD MNE + ISO 37001 + EU 2019/1937 sub-rubric |
| Input shape | `dataset/supplier-disclosure-pack-schema` + `schemas/supplier-disclosure-pack.schema.json` | Canonical JSON Schema for the supplier disclosure pack + 3 synthetic samples for testing |
| Grading pipeline | `pipeline/supplier-policy-grading` | Persona → PII redact → 3 GREP packs (S+E+G) → 3 RAG passes (regulatory + corridors + lead code) → judge → propose remediation |
| Multi-tier audit | `pipeline/deep-tier-supplier-audit` | Walks T1 → T4+ with `processor/iterative-revise-loop`; escalates high-severity |
| Cross-org sharing | `pipeline/anonymized-illicit-recruitment-pattern-sharing` | k-anonymity gate before hub-sharing systemic broker / corridor patterns |
| Cross-org pattern | `pattern/k-anonymity-aggregation` | Generalized k-anonymity + HMACed-key + optional DP-noise design pattern |
| Live lookup tool | `tool/cbp-wro-lookup` | US CBP WRO + UFLPA Entity List check; HALT on hit |
| Regression bench | `benchmark/esg-supplier-grading-bench` | Runs the grading pipeline against the 3 synthetic disclosure packs across 2 model arms (Ollama-Llama-3-8B vs vLLM-Qwen-2.5-32B-AWQ); per-dimension reporting |

## End-to-end flow

```
[Supplier disclosure pack]
        │
        ▼ rule-pack/privacy-pii-text-en + processor/redact-pii-text
[PII-redacted text]
        │
        ▼ rule-pack/grep-esg-forced-labor-red-flags
[Red-flag hits with severity + category]
        │
        ▼ rule-pack/hybrid-retrieval-policy → knowledge-pack/csddd-and-forced-labor-indicators
[ILO + CSDDD + national-code citations]
        │
        ▼ rule-pack/hybrid-retrieval-policy → lead-company code of conduct
[Lead-code citations]
        │
        ▼ processor/llm-judge + rubric/esg-supplier-compliance-v1
[Structured findings: severity, indicator, evidence, tier, remediation]
        │
        ▼ harness/text-safety-review (with persona/esg-auditor)
[CSDDD Art. 10 remediation proposal: corrective action, supplier right of reply, 60-day milestone]
        │
        ▼ processor/audit-trace-emitter
[Audit trace for board oversight per CSDDD Art. 26]
```

## How tier 3 / tier 4+ traversal works

`pipeline/deep-tier-supplier-audit` uses `processor/iterative-revise-loop`
as the outer agent:

1. **Iter 1**: Resolve T1 supplier → grade T1 → expand T1's known T2 set.
2. **Iter 2**: For each T2, grade → expand T3 set.
3. **Iter N**: Grade T(N-1) → expand T(N) set. **Surface audit_gaps**
   when a tier cannot be resolved (typical at T ≥ 3 - most factories
   in Asia subcontract through informal labor agencies whose books
   don't surface in the lead supplier registry).
4. **Termination**: max_depth reached OR every leaf resolved.
5. **Aggregation**: `processor/multi-vector-fusion` rolls up per-tier
   findings into a chain-wide compliance report.
6. **Escalation**: `processor/escalate-human-review` routes any
   high-severity finding to the compliance team.

## Cross-organization knowledge sharing (without breaching confidentiality)

`pipeline/anonymized-illicit-recruitment-pattern-sharing` implements a
k-anonymity + HMAC scheme:

1. Each org's findings → `processor/redact-pii-text` (worker names
   stripped).
2. Broker IDs → HMACed with hub-published salt (so same broker
   produces same hash everywhere, but the hash is not invertible).
3. Bucketed by `(broker_hash, corridor, indicator_category,
   90-day-window)`.
4. Buckets with `count < k` (default k = 5) are dropped - small
   buckets could be re-identified back to the source org.
5. Surviving buckets are signed and published.
6. Member orgs query: "have these indicators been seen against this
   broker / corridor?" → returns aggregate count + severity, never
   per-org provenance.

Inspired by FATF Recommendation 18 info-sharing principles, adapted
to the ESG / forced-labor context. The k threshold is a tunable
trade-off: higher k = stronger anonymity, weaker signal; lower k =
faster pattern surfacing, more re-identification risk.

## Evidence the GREP rules work (live test, 2026-05-19)

Run `python3 scripts/run_esg_grep.py` against the 3 synthetic samples
in `data/supplier-disclosure-samples/` - output:

```
=== sample-T1-tech-supplier-good.json ===
  S (forced-labor): no hits
  E (environmental): no hits
  G (governance): no hits

=== sample-T2-agri-paraguay-mixed.json ===
  E (environmental): 2 rules fired
     high     : land_clearing_legacy, near_protected_area

=== sample-T3-textile-mae-sot-flagged.json ===
  S (forced-labor): 8 rules fired
     critical : passport_retention, restricted_movement_dormitory
     high     : recruitment_fee_abuse, wage_withholding,
                isolation_unfree_communication, abusive_overtime_consent
     medium   : excessive_overtime, audit_gap_tier_3_4
  E (environmental): 1 rules fired
     critical : untreated_dye_effluent
  G (governance): 1 rules fired
     high     : beneficial_ownership_opaque

=== headline ===
  T1-good                            C: 0  H: 0  M: 0  L: 0  (correctly clean)
  T2-mixed                           C: 0  H: 2  M: 0  L: 0  (deforestation legacy + KBA)
  T3-Mae-Sot-flagged                 C: 3  H: 5  M: 2  L: 0  (10 hits, all expected)
```

Captured findings JSON at `data/esg-grep-findings.json`. The rules
correctly:
1. Stay silent on the well-disclosed T1 supplier (zero false positives).
2. Surface 2 high-severity environmental flags on the Paraguay T2 soy
   supplier (legacy land clearing + protected-area proximity).
3. Detect 10 indicators across all 3 ESG dimensions on the T3 Mae
   Sot textile workshop, including all 3 critical-severity rules
   expected: passport retention, dormitory movement restriction,
   untreated dye effluent.

The `processor/structured-to-prose` step (added 2026-05-19 after the
first test exposed false negatives on structured JSON) flattens the
supplier disclosure into prose lines before GREP - this is what
makes structured red-flag detection work.

## What this is NOT

- A legal opinion. Real CSDDD compliance requires jurisdiction-
  specific legal sign-off, BSA-officer-equivalent review, and CSDDD
  Art. 26 board-level oversight.
- A determination of forced labor. The pipeline produces RISK FLAGS
  with citations. The lead company's compliance officer makes the
  determination after the supplier's right of reply (CSDDD Art. 10).
- A substitute for on-the-ground audits at high-risk tiers - those
  remain mandatory under CSDDD risk-based due diligence.

## Reference for proposers of this use case

Catalog: `github.com/Amarel-Taylor-Scott/open-harness-hub`. All components
listed above validate against `schemas/` and emit to 13 standards
formats (Croissant, MCP, Agent Skills, HF cards, lm-eval-harness,
promptfoo, CycloneDX-ML, OpenLineage, C2PA, EU AI Act, SPDX 3.0,
JSON-LD, DPV).

The CSDDD-aligned pack is `lifecycle: experimental` - feedback
welcome on indicator coverage, multi-lingual GREP patterns, and the
k-anonymity threshold default.
