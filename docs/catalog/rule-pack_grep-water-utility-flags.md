# Water utility SDWA / LCRR / AWIA red-flag detectors

*rule-pack* · `rule-pack/grep-water-utility-flags` · v0.1.0 · beta

GREP detectors for SDWA compliance gaps + acute risks.

| axis | value |
|---|---|
| industry | water_utility, water_utility.lcr, water_utility.sdwa |
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
| `e_coli_mcl_violation` | critical | water.acute.e_coli | `(?i)(?:e[\.\s]\s*coli|escherichia\s+coli|fecal\s+coliform)\s+(?:positive|dete...` |
| `nitrate_above_mcl` | critical | water.acute.nitrate | `(?i)nitrate.{0,40}(?:\d{1,2}(?:\.\d+)?)\s*mg(?:/|\s*per\s*)?l(?!.{0,200}below...` |
| `lead_above_al` | critical | water.lead.action_level_exceeded | `(?i)lead\s+(?:90th[- ]?percentile|al|action\s+level)\s+(?:exceed|over|above|>...` |
| `lcrr_inventory_missing` | critical | water.lcrr.no_inventory | `(?i)(?:lead\s+service\s+line\s+inventory|lsli|lsl\s+inventory)\s+(?:not\s+(?:...` |
| `pn_tier_1_missed` | critical | water.public_notification.tier_1_missed | `(?i)tier\s+1\s+(?:public\s+)?notification\s+(?:missed|past\s+24\s+hours|not\s...` |
| `awia_rra_overdue` | high | water.awia.rra_overdue | `(?i)(?:awia\s+)?(?:risk\s+and\s+resilience\s+assessment|rra)\s+(?:overdue|exp...` |
| `scada_default_credentials` | critical | water.scada.default_credentials | `(?i)scada\s+(?:system|hmi|plc)\s+(?:default\s+(?:password|credentials)|unchan...` |
| `ccr_missing` | high | water.ccr.missing | `(?i)(?:consumer\s+confidence\s+report|ccr)\s+(?:not\s+(?:issued|published)|mi...` |
| `trihalomethane_mcl` | high | water.dbpr.tthm_mcl | `(?i)(?:tthm|trihalomethanes?|total\s+thm)\s+(?:above|exceed|violation)\s+\d{1...` |
| `haa5_mcl` | high | water.dbpr.haa5_mcl | `(?i)(?:haa5|haloacetic\s+acids?)\s+(?:above|exceed|violation)\s+\d{1,3}\s*(?:...` |
| `tt_violation_filtration` | high | water.tt.filtration | `(?i)(?:filtration|treatment\s+technique|tt)\s+(?:violation|failure)|turbidity...` |
| `monitoring_skipped` | medium | water.monitoring.skipped | `(?i)(?:monitoring|sampling)\s+(?:not\s+(?:performed|conducted)|skipped|missed...` |

