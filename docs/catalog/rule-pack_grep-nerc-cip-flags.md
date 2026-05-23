# NERC CIP compliance red-flag detectors

*rule-pack* · `rule-pack/grep-nerc-cip-flags` · v0.1.0 · beta

Detectors for NERC CIP gaps.

| axis | value |
|---|---|
| industry | energy, energy.grid, security, compliance |
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
| `no_baseline_config` | critical | energy.cip.no_baseline | `(?i)(?:no|absent|missing)\s+baseline\s+configuration|baseline\s+configuration...` |
| `unauthorized_firmware` | critical | energy.cip.unauthorized_firmware | `(?i)unauthorized\s+(?:firmware|software|patch)|firmware\s+(?:installed|deploy...` |
| `expired_authorization` | high | energy.cip.expired_authorization | `(?i)(?:user\s+)?authorization\s+(?:expired|lapsed|past\s+due)|access\s+(?:not...` |
| `esp_gap` | critical | energy.cip.esp_gap | `(?i)(?:electronic\s+security\s+perimeter|\besp\b)\s+(?:gap|inactive|disabled|...` |
| `psp_gap` | critical | energy.cip.psp_gap | `(?i)(?:physical\s+security\s+perimeter|\bpsp\b)\s+(?:breach|unauthorized\s+ac...` |
| `unpatched_vuln_35d` | high | energy.cip.unpatched_35d | `(?i)(?:unpatched|outstanding)\s+(?:vulnerability|cve)\s+(?:over|exceed(?:ing|...` |
| `no_irp` | high | energy.cip.no_incident_plan | `(?i)(?:no|absent|missing)\s+(?:cyber\s+)?incident\s+response\s+plan|cip[- ]?0...` |
| `no_recovery_plan` | high | energy.cip.no_recovery_plan | `(?i)(?:no|absent|missing|untested)\s+recovery\s+plan|cip[- ]?009\s+plan\s+(?:...` |
| `supply_chain_risk_unassessed` | medium | energy.cip.supply_chain | `(?i)(?:vendor|supplier|supply[- ]?chain)\s+(?:risk|cyber)\s+(?:not\s+(?:asses...` |
| `bes_cyber_uncategorized` | critical | energy.cip.no_categorization | `(?i)bes\s+cyber\s+(?:asset|system)\s+(?:not\s+categorized|impact\s+rating\s+(...` |
| `personnel_risk_assessment_lapsed` | high | energy.cip.pra_lapsed | `(?i)(?:personnel\s+)?risk\s+assessment\s+(?:lapsed|overdue|past\s+due)|crimin...` |
| `removable_media_uncontrolled` | high | energy.cip.removable_media | `(?i)(?<!no\s)\b(?:removable\s+media|usb\s+drives?|portable\s+drives?)\s+(?:un...` |

