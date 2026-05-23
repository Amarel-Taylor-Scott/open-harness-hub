# Food safety / FSMA / HACCP red-flag detectors

*rule-pack* · `rule-pack/grep-food-safety-flags` · v0.1.0 · beta

Detectors for FSMA + HACCP non-compliance.

| axis | value |
|---|---|
| industry | food_safety, food_safety.fsma, food_safety.haccp, compliance |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `ccp_deviation_not_documented` | critical | food_safety.haccp.ccp_deviation | `(?i)ccp\s+deviation(?!\s+(?:documented|corrective\s+action|recorded))` |
| `haccp_plan_missing` | critical | food_safety.haccp.no_plan | `(?i)(?:no|absent|missing)\s+haccp\s+plan|haccp\s+plan\s+(?:not\s+(?:documente...` |
| `fsvp_missing` | critical | food_safety.fsma.fsvp_missing | `(?i)(?:no|absent)\s+fsvp(?!\s+(?:exemption|not\s+required))|foreign\s+supplie...` |
| `preventive_controls_missing` | high | food_safety.fsma.pchf_missing | `(?i)(?:no|absent)\s+preventive\s+controls|preventive\s+controls\s+(?:not\s+(?...` |
| `recall_class_i` | critical | food_safety.recall.class_i | `(?i)class\s+i\s+recall|life[- ]?threatening\s+(?:adulteration|misbranding)|un...` |
| `pathogen_positive` | critical | food_safety.pathogen | `(?i)(?:listeria\s+monocytogenes|salmonella|e[\.\s]\s*coli\s+o157|stec|cyclosp...` |
| `monitoring_gap` | high | food_safety.haccp.monitoring_gap | `(?i)(?:no|missing|gap\s+in)\s+(?:ccp|cooler|temperature|cleanability)\s+monit...` |
| `ftl_no_traceability` | high | food_safety.fsma.no_traceability | `(?i)(?:no|absent|incomplete)\s+traceability\s+(?:for|on)\s+(?:ftl|food\s+trac...` |
| `sanitation_failure` | high | food_safety.sanitation | `(?i)(?:sanitation|cleaning|sso)\s+(?:failure|noncompliance|verification\s+fai...` |
| `allergen_cross_contact` | high | food_safety.allergen | `(?i)allergen\s+cross[- ]?contact(?:\s+(?:incident|risk|controls\s+missing))?` |
| `training_lapsed` | medium | food_safety.training_lapsed | `(?i)(?:food[- ]?safety|qualified\s+individual|pcqi)\s+training\s+(?:lapsed|ov...` |
| `supplier_audit_missing` | medium | food_safety.fsvp.supplier_audit_missing | `(?i)(?:no|absent)\s+supplier\s+audit\s+(?:in\s+past\s+12\s+months|completed)|...` |

