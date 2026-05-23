# Insurance claim fraud red-flag detectors (NAIC + CAIF)

*rule-pack* · `rule-pack/grep-insurance-fraud-red-flags` · v0.1.0 · beta

GREP detectors for the highest-leverage insurance-claim fraud
red flags drawn from NAIC fraud-fighter handbook + Coalition
Against Insurance Fraud indicators. Pair with
`pipeline/insurance-claim-review`.

| axis | value |
|---|---|
| industry | insurance, insurance.claims, insurance.fraud, finance |
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
| `recent_coverage_change` | critical | insurance.fraud.recent_coverage_change | `(?i)(coverage\s+(?:increased|upgraded|added|amended)|policy\s+(?:increased|up...` |
| `loss_at_renewal` | high | insurance.fraud.loss_at_renewal | `(?i)loss\s+(?:occurred|reported)\s+(?:within|less than)\s+\d{1,3}\s+days?\s+(...` |
| `claimant_on_fraud_watchlist` | critical | insurance.fraud.claimant_watchlist | `(?i)claimant\s+on\s+(?:internal\s+)?fraud\s+(?:watch[- ]?list|flag\s+list)|pr...` |
| `conflicting_witness` | high | insurance.fraud.conflicting_witness | `(?i)witness\s+statements?\s+(?:conflict|contradict|inconsistent|disagree)|two...` |
| `photos_predate_loss` | critical | insurance.fraud.photo_metadata | `(?i)photos?\s+(?:pre[- ]?date|predating|taken before|exif\s+date\s+(?:before|...` |
| `inflated_invoice` | high | insurance.fraud.inflated_invoice | `(?i)(?:repair|invoice|estimate)\s+(?:significantly\s+)?(?:above|exceeds)\s+(?...` |
| `shop_on_flag_list` | high | insurance.fraud.provider_flagged | `(?i)(?:repair\s+shop|provider|vendor)\s+(?:on|flagged on)\s+(?:internal\s+)?(...` |
| `missing_police_report` | medium | insurance.fraud.no_police_report | `(?i)(?:no|absent|not\s+filed|n[\.\/]?a)\s+police\s+report(?!.{0,120}(minor|un...` |
| `claimant_relationship_to_witness` | medium | insurance.fraud.witness_relationship | `(?i)witness\s+(?:is|was)\s+(?:family|spouse|relative|business partner|employe...` |
| `ssn_in_claim_body` | high | phi.ssn_unredacted | `(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)` |
| `phantom_damage_pattern` | critical | insurance.fraud.phantom_damage | `(?i)damage\s+(?:not\s+consistent|inconsistent)\s+with\s+(?:reported|alleged)\...` |
| `multiple_claims_short_window` | high | insurance.fraud.serial_claims | `(?i)(\d+|\bmultiple\b|several)\s+(?:prior\s+)?claims?\s+(?:filed|submitted)\s...` |

