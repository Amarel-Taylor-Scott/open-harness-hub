# Cannabis compliance flags (METRC + §280E + FinCEN + COA)

*rule-pack* · `rule-pack/grep-cannabis-compliance-flags` · v0.1.0 · beta

Detectors for cannabis-industry compliance gaps.

| axis | value |
|---|---|
| industry | cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing |
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
| `interstate_transport_violation` | critical | cannabis.federal.interstate | `(?i)(?:driven|transported|shipped)[\s\S]{0,80}?(?:across|over)\s+(?:state\s+(...` |
| `section_280e_deduction` | critical | cannabis.tax.280e | `(?i)(?:deducted|claimed)[\s\S]{0,120}?(?:ordinary\s+(?:advertising|rent|payro...` |
| `metrc_variance_unreported` | critical | cannabis.metrc.variance_unreported | `(?i)metrc\s+(?:variance|discrepancy|inventory\s+(?:gap|mismatch))[\s\S]{0,120...` |
| `transport_manifest_missing` | high | cannabis.transport.no_manifest | `(?i)(?:left|departed)[\s\S]{0,120}?(?:premises|manufacturing)\s+without\s+(?:...` |
| `coa_missing_or_expired` | critical | cannabis.coa.missing | `(?i)(?:no\s+current\s+(?:pesticide|microbial|heavy\s+metal|solvent)\s+panel|c...` |
| `potency_label_variance_excess` | high | cannabis.label.potency_variance | `(?i)thc\s+(?:potency\s+)?(?:of\s+)?[2-9][0-9]%\s+on\s+the\s+label[\s\S]{0,120...` |
| `youth_appealing_packaging` | critical | cannabis.packaging.youth | `(?i)(?:cartoon\s+(?:bear|character|animal|graphic)|candy\s+resemblance|market...` |
| `non_child_resistant_packaging` | critical | cannabis.packaging.crp | `(?i)(?:lacked|missing|no)\s+child[- ]?resistant\s+(?:certification|packaging)...` |
| `cash_over_10k_no_sar_ctr` | high | cannabis.fincen.no_sar_ctr | `(?i)(?:\$1[0-9],[0-9]{3}|\$[2-9][0-9],[0-9]{3}|\$1[0-9]{4}|cash\s+(?:deposit|...` |
| `buffer_zone_school_violation` | high | cannabis.zoning.school_buffer | `(?i)(?:under|below)\s+(?:the\s+)?(?:600|1000)\s*(?:ft|feet)\s+(?:state\s+)?(?...` |
| `agent_badge_expired` | medium | cannabis.badge.expired | `(?i)(?:agent|employee)\s+(?:badge|registration|card)\s+(?:expired|lapsed|inac...` |

