# Syndromic risk-tier classifier (Green / Yellow / Red escalation)

*rule-pack* · `rule-pack/syndromic-risk-tier` · v0.1.0 · experimental

Classifier rule pack for offline syndromic triage. Evaluates a structured
symptom bundle (syndrome label, case count, alert threshold ratio, severity
flags) produced by the AfyaEdge intake processor and emits a risk tier:

  Green  — below alert threshold; monitor, no immediate escalation.
  Yellow — at or approaching alert threshold (≥50% of threshold); notify
           district health officer within 24 hours.
  Red    — at or exceeding alert threshold, or any priority-1 syndrome
           regardless of count (e.g. acute haemorrhagic fever, meningitis
           with ≥2 cases in same locality); immediate MoH notification
           required and sync queued on reconnect.

Rules apply the WHO IDSR 3rd edition alert thresholds encoded in the
syndromic-surveillance-case-definitions Knowledge Corpus. The rule pack
is deterministic — no LLM sampling involved in tier assignment.

DEFENSIVE INGESTION CONTRACT:
- Tier decisions are decision-SUPPORT outputs, not clinical diagnoses.
- A "Green" tier never means "no disease" — it means below notification
  threshold at time of assessment.
- Any pipeline consuming this rule pack MUST surface: "Tier assignment
  is a surveillance aid only. Consult a trained health officer. Report
  suspected outbreaks per your country's IDSR obligations."
- The rule pack does not handle laboratory confirmation; it operates on
  syndromic case counts only.

CAPABILITY LIFT (structural): deterministic tier assignment from symptom
counts prevents the model from producing inconsistent escalation decisions
— a base LLM will produce different thresholds on different runs for the
same inputs. This is a sub_token arithmetic guarantee (comparing counts
to thresholds). lift_reason: deterministic_guarantee; mechanism: sub_token.

| axis | value |
|---|---|
| industry | healthcare.public_health, public_safety, government.regulatory |
| capability | classification, safety_gating, routing |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | Apache-2.0 |



**family:** `classifier`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `priority1_syndrome_immediate` | critical | tier.red.priority1 | `case.syndrome_label IN ['acute_haemorrhagic_fever', 'human_rabies', 'polio'] ...` |
| `meningitis_cluster_red` | critical | tier.red.cluster | `case.syndrome_label == 'meningitis_syndrome' AND case.rolling_7d_count >= 2 A...` |
| `threshold_exceeded_red` | high | tier.red.threshold | `case.threshold_ratio >= 1.0` |
| `threshold_approaching_yellow` | medium | tier.yellow.approaching | `case.threshold_ratio >= 0.5 AND case.threshold_ratio < 1.0` |
| `severity_flag_yellow` | medium | tier.yellow.severity | `case.severe_outcome_flag == true AND case.threshold_ratio < 1.0` |
| `below_threshold_green` | low | tier.green | `case.threshold_ratio < 0.5 AND case.severe_outcome_flag == false AND case.syn...` |

