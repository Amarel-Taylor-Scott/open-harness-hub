# Clinical red flags

*rule-pack* · `rule-pack/clinical-red-flags` · v0.1.0 · experimental

A classifier rule pack of presenting-symptom patterns that require
immediate clinical evaluation. Fires inside the clinical-decision-
support harness BEFORE differential reasoning, so the assistant's
first sentence can flag the red flag.

Educational baseline; covered entities should layer
institution-specific rules and update against the latest guidelines.

| axis | value |
|---|---|
| industry | healthcare, healthcare.clinical |
| capability | classification, safety_gating |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `classifier`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `chest_pain_with_radiation` | critical | red_flag.acs_or_dissection | `` |
| `sudden_severe_headache` | critical | red_flag.sah | `` |
| `focal_neuro_deficit` | critical | red_flag.stroke | `` |
| `anaphylaxis_pattern` | critical | red_flag.anaphylaxis | `` |
| `pregnancy_bleeding_acute` | critical | red_flag.ob_emergency | `` |
| `suicide_intent_active` | critical | red_flag.psych_emergency | `` |

