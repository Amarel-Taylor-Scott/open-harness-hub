# Radiology report quality + incidental-findings red flags

*rule-pack* · `rule-pack/grep-radiology-report-red-flags` · v0.1.0 · beta

GREP detectors for radiology-report quality and incidental-finding
follow-up gaps. Designed to be run AFTER `rule-pack/privacy-phi-
hipaa-en` redaction. Pair with `pipeline/radiology-report-grading`.

Categories:
 - **incidental-findings**: thyroid / adrenal / renal / pulmonary
   nodules flagged without follow-up recommendation
 - **missing-RADS-score**: report describes a finding in a system
   that has a RADS (BI-/LI-/TI-/O-/PI-/Lung-) but omits the score
 - **definitive-without-differential**: report uses "is" rather
   than hedged "consistent with" for non-pathognomonic findings
 - **missing-comparison**: prior available but not compared
 - **fleischner-noncompliance**: pulmonary nodule >= 6 mm without
   correct Fleischner follow-up timing

Heuristic — TRIGGER review, not block.

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology |
| capability | safety_gating, classification, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `thyroid_nodule_without_tirads` | high | radiology.missing_rads.thyroid | `(?is)thyroid.{0,30}nodule(?!.{0,400}\b(TR\s?[1-5]|TIRADS|TI-RADS)\b)` |
| `breast_mass_without_birads` | high | radiology.missing_rads.breast | `(?is)\b(breast)\b.{0,80}\b(mass|lesion)\b(?!.{0,1200}\b(BIRADS|BI-RADS|BI\s*R...` |
| `liver_observation_without_lirads` | medium | radiology.missing_rads.liver | `(?is)(?<!no\s)(?<!no\sincidental\s)(?<!without\s)(?<!absent\s)(?<!negative\sf...` |
| `pulm_nodule_without_fleischner_followup` | high | radiology.missing_followup.pulm_nodule | `(?is)(?:(\d+(?:\.\d+)?\s*mm)\b\s+\b(?:sub-solid|solid|ground-glass|part-solid...` |
| `adrenal_incidentaloma_without_workup` | medium | radiology.incidental.adrenal | `(?is)adrenal.{0,30}(mass|nodule|incidentaloma)(?!.{0,400}(< ?10\s*HU|hounsfie...` |
| `renal_lesion_without_bosniak` | low | radiology.missing_rads.renal | `(?is)renal.{0,30}(cyst|mass|lesion)(?!.{0,400}\bbosniak\b)` |
| `definitive_without_differential` | medium | radiology.definitive_without_differential | `(?is)\b(is|are)\s+(?:a |an )?(?:metastasis|adenocarcinoma|hcc|hepatocellular|...` |
| `no_comparison_when_prior_available` | medium | radiology.missing_comparison | `(?is)(prior\s+(?:study|exam|imaging|CT|MRI)\s+(?:available|on file|in system)...` |
| `impression_lacks_recommendation` | medium | radiology.missing_recommendation | `(?is)\bimpression\b\s*[:\.]?(?:(?!\brecommend|\bsuggest|\bnext\b|\bfollow[- ]...` |
| `phi_unredacted_signature_block` | critical | phi.unredacted | `(?i)(MRN|medical record number|date of birth|dob)[: ]\s*[A-Z0-9-]+` |
| `lung_nodule_below_fleischner_threshold_no_disposition` | low | radiology.fleischner.small_nodule_disposition | `(?is)pulmonary\s+nodule.{0,80}([0-5](?:\.\d+)?\s*mm)(?!.{0,400}(no follow-up|...` |

