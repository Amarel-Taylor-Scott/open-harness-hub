# Benefits-eligibility red-flag detectors (SNAP / Medicaid / UI)

*rule-pack* · `rule-pack/grep-benefits-eligibility-flags` · v0.1.0 · beta

GREP detectors for the highest-leverage benefits-eligibility
signals: countable-income markers above thresholds, asset
deemers, undisclosed household members, immigration-status
questions, missing documentation, possible duplicate enrollment.

| axis | value |
|---|---|
| industry | government, government.benefits, compliance |
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
| `high_countable_income` | medium | benefits.income.high_countable | `(?i)(monthly|gross|wage|salary)\s+income\s*[:=]\s*\$?\s*([4-9]\d{3,}|\d{5,})` |
| `asset_above_resource_limit` | medium | benefits.asset.above_limit | `(?i)(asset|resource|bank\s+account|savings)\s+total\s*[:=]\s*\$?\s*([4-9]\d{3...` |
| `undisclosed_household_member` | high | benefits.household.undisclosed_member | `(?i)(other|additional|undisclosed)\s+(?:adult|household\s+member|person)\s+(?...` |
| `missing_documentation` | low | benefits.documentation.missing | `(?i)(?:no|missing|absent|not provided)\s+(?:proof|documentation|verification)...` |
| `duplicate_enrollment_pattern` | high | benefits.duplicate_enrollment | `(?i)(prior|existing|active)\s+(?:enrollment|case)\s+(?:in\s+)?(?:another|othe...` |
| `able_bodied_work_req` | medium | benefits.work_requirement.unmet | `(?i)(?:no|absent)\s+(?:work|training|community\s+service)\s+(?:participation|...` |
| `ssn_unredacted` | high | phi.ssn_unredacted | `(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)` |
| `self_employment_unreported` | high | benefits.income.self_employment_unreported | `(?i)self[- ]?employ\w+.{0,80}(?:not reported|unreported|n[\.\/]?a)|gig\s+inco...` |
| `fraud_warrant_outstanding` | critical | benefits.fraud.warrant_outstanding | `(?i)(?:fraud|public assistance fraud|welfare fraud)\s+(?:warrant|investigatio...` |

