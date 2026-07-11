# Drug interaction severity classifier (defensive; RxNorm / DrugBank-aligned)

*rule-pack* · `rule-pack/drug-interaction-severity` · v0.1.0 · experimental

Classifier rule pack for on-device medicine-label safety pipelines (e.g.
MedLabel). Evaluates a pair (new_drug, existing_medication_list) against
known interaction patterns drawn from public RxNorm interaction data and
publicly documented DrugBank interaction categories. Emits a severity tier:

  none     — no known interaction in reference corpus.
  minor    — interaction documented but unlikely to cause harm at standard doses;
             note in warning.
  moderate — interaction may require dose adjustment or monitoring; recommend
             pharmacist review.
  severe   — contraindicated combination; high risk of adverse outcome; emit
             STOP override and mandatory "consult a doctor or pharmacist
             immediately" instruction.

DEFENSIVE INGESTION CONTRACT:
- This rule pack is a decision-support reference only. It does NOT replace
  pharmacist review, clinical judgement, or a regulated drug interaction
  database with full coverage.
- Coverage is limited to the most clinically significant public-domain
  interaction pairs. Many drug combinations are NOT covered — absence of a
  finding is NOT a safety clearance.
- Every pipeline consuming this rule pack MUST surface: "Drug interaction
  check is for information only. Always consult a qualified pharmacist or
  doctor before taking any medication. This tool does not provide medical
  advice."
- Volatile facts (e.g., newly discovered interactions, updated dosing
  guidelines) require periodic corpus refresh. Mark freshness as 'volatile'.

CAPABILITY LIFT (structural): a base language model asked to recall drug
interactions will hallucinate or miss interactions because: (a) interaction
data requires pairing across all n² combinations — a long-tail recall task
the model cannot reliably perform; (b) the severe/contraindicated boundary
must be deterministic, not sampled. This rule pack provides the lookup
table outside the model. lift_reason: no_addressable_source (offline —
cannot query RxNav API) + deterministic_guarantee (severity must be exact,
not sampled); mechanism: context_length (full drug interaction matrix
cannot fit in implicit model memory).

| axis | value |
|---|---|
| industry | healthcare, healthcare.pharmacy, humanitarian |
| capability | classification, safety_gating, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | Apache-2.0 |



**family:** `classifier`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `severe_contraindicated_maoi_ssri` | critical | interaction.serotonin_syndrome | `drug_class(new_drug) == 'maoi' AND any(drug_class(d) == 'ssri_snri' for d in ...` |
| `severe_contraindicated_anticoagulant_nsaid` | critical | interaction.major_bleed | `drug_class(new_drug) == 'nsaid' AND any(drug_class(d) IN ['warfarin', 'doac']...` |
| `severe_contraindicated_maoi_sympathomimetic` | critical | interaction.hypertensive_crisis | `drug_class(new_drug) == 'sympathomimetic' AND any(drug_class(d) == 'maoi' for...` |
| `severe_qt_prolonging_combination` | critical | interaction.qt_prolongation | `qt_risk(new_drug) == 'known' AND sum(qt_risk(d) == 'known' for d in existing_...` |
| `moderate_statin_cyp3a4_inhibitor` | high | interaction.myopathy_risk | `drug_class(new_drug) == 'statin_cyp3a4_sensitive' AND any(cyp3a4_inhibitor_st...` |
| `moderate_nsaid_antihypertensive` | medium | interaction.bp_renal | `drug_class(new_drug) == 'nsaid' AND any(drug_class(d) IN ['ace_inhibitor', 'a...` |
| `minor_noted` | low | interaction.minor | `interaction_known(new_drug, existing_meds) == 'minor'` |
| `no_interaction_found` | info | interaction.none | `interaction_known(new_drug, existing_meds) == 'none'` |

