# Gaming integrity / AML / responsible-gambling flags

*rule-pack* · `rule-pack/grep-gaming-integrity-flags` · v0.1.0 · beta

Detectors for gaming compliance gaps.

| axis | value |
|---|---|
| industry | gaming, gaming.aml, gaming.responsible_gambling |
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
| `self_excluded_player` | critical | gaming.self_exclusion.hit | `(?i)player\s+(?:on\s+)?(?:self[- ]?exclusion|exclusion)\s+list|opted[- ]?out\...` |
| `ctr_aggregation_threshold` | critical | gaming.aml.ctr_threshold | `(?i)(?:cash\s+transaction|aggregated|aggregate)\s+(?:total|amount)\s+(?:over|...` |
| `structuring_indicator` | critical | gaming.aml.structuring | `(?i)multiple\s+(?:transactions?|cash\s+(?:in|out))\s+(?:just\s+below|under)\s...` |
| `rapid_loss_velocity` | high | gaming.responsible_gambling.rapid_loss | `(?i)(?:loss(?:es)?|wagers?)\s+(?:exceed|over|>)\s+\$?\s*\d{4,}\s+(?:in|within...` |
| `deposit_limit_override` | high | gaming.responsible_gambling.limit_override | `(?i)deposit\s+limit\s+(?:override|bypassed|disabled|removed)` |
| `sar_threshold_unfilled` | critical | gaming.aml.sar_unfilled | `(?i)(?:sar|suspicious\s+activity\s+report)\s+(?:threshold\s+)?(?:not\s+(?:fil...` |
| `source_of_funds_gap` | high | gaming.aml.sof_gap | `(?i)source[- ]?of[- ]?funds\s+(?:not\s+verified|missing|gap)\s+(?:on|for)\s+(...` |
| `minor_age_verification_gap` | critical | gaming.minor_protection | `(?i)age\s+verification\s+(?:not\s+(?:performed|completed)|skipped|gap)|under[...` |
| `license_expiration` | high | gaming.licensing.expired | `(?i)(?:gaming\s+)?license\s+(?:expired|past\s+(?:renewal|due)|expires?\s+(?:i...` |
| `ssn_in_player_record` | high | gaming.pii.ssn_unredacted | `(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)` |
| `match_fixing_indicator` | critical | gaming.integrity.match_fixing | `(?i)(?:match[- ]?fixing|game[- ]?fixing|insider[- ]?information)\s+(?:indicat...` |
| `vip_host_red_flag` | high | gaming.aml.vip_override | `(?i)vip\s+(?:host|comp)\s+(?:bypass|override)\s+(?:limit|kyc|verification)` |

