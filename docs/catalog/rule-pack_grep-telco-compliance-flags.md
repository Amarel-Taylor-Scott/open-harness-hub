# Telco compliance red-flag detectors (FCC / CPNI / CALEA)

*rule-pack* · `rule-pack/grep-telco-compliance-flags` · v0.1.0 · beta

Detectors for telco regulatory gaps.

| axis | value |
|---|---|
| industry | telecommunications, telecommunications.fcc, telecommunications.cpni |
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
| `cpni_breach_unreported_7d` | critical | telco.cpni.breach_unreported | `(?i)cpni\s+breach[\s\S]{0,500}?(?:not\s+(?:yet\s+)?(?:reported|notified|filed...` |
| `cpni_used_for_marketing_no_optin` | critical | telco.cpni.no_optin | `(?i)cpni\s+(?:used|shared)\s+for\s+marketing(?!.{0,200}(?:opt[- ]?in|customer...` |
| `stir_shaken_missing` | critical | telco.fcc.stir_shaken_missing | `(?i)stir[-/ ]?shaken\s+(?:not\s+(?:implemented|attesting|signing)|missing|abs...` |
| `nors_outage_unreported_120min` | critical | telco.fcc.nors_late | `(?i)(?:nors|network\s+outage|initial\s+outage\s+report)\s+(?:report\s+)?(?:pa...` |
| `calea_lawful_intercept_not_ready` | high | telco.calea.not_ready | `(?i)calea\s+(?:lawful[- ]?intercept\s+(?:capability\s+)?)?(?:not\s+(?:ready|i...` |
| `e911_reliability_gap` | critical | telco.e911.reliability | `(?i)e911\s+(?:reliability|location[- ]?accuracy)\s+(?:gap|below|fail)|enhance...` |
| `data_retention_violation` | high | telco.data_retention | `(?i)(?:cpni|billing|call[- ]?detail)\s+records?\s+(?:retained|kept)\s+(?:beyo...` |
| `robocall_threshold_complaints` | high | telco.robocall.complaints | `(?i)robocall\s+(?:complaints?|violations?)\s+(?:exceed|over|above)\s+(?:thres...` |
| `tcpa_violation_indicator` | high | telco.tcpa | `(?i)tcpa\s+(?:violation|noncompliance|class[- ]?action)|automated[- ]?dial(?:...` |
| `spectrum_auction_compliance` | medium | telco.spectrum.license | `(?i)(?:spectrum|frequency)\s+(?:license|allocation)\s+(?:expired|past\s+renew...` |

