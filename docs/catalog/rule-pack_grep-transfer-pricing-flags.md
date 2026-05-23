# Transfer-pricing red-flag detectors (OECD / §482 / BEPS)

*rule-pack* · `rule-pack/grep-transfer-pricing-flags` · v0.1.0 · beta

Detectors for transfer-pricing risk.

| axis | value |
|---|---|
| industry | tax, tax.transfer_pricing, finance |
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
| `no_benchmarking_study` | critical | tax.tp.no_benchmarking | `(?i)(?:no|absent|missing)\s+benchmarking\s+(?:study|analysis)|comparables\s+(...` |
| `embedded_royalty_no_ip` | high | tax.tp.embedded_royalty | `(?i)(?:embedded\s+royalty|hidden\s+royalty)\s+(?:without|absent)\s+(?:ip\s+(?...` |
| `captive_insurance_no_risk` | high | tax.tp.captive_no_risk | `(?i)captive\s+insurance(?:\s+(?:company|reinsurance))?(?!.{0,200}(?:risk\s+tr...` |
| `loss_making_lrd` | critical | tax.tp.loss_making_lrd | `(?i)(?:limited[- ]?risk\s+distributor|lrd)\s+(?:loss[- ]?making|negative\s+ma...` |
| `cash_pool_below_arm_length` | high | tax.tp.cash_pool_interest | `(?i)cash[- ]?pool(?:ing)?\s+(?:interest|rate)\s+(?:below\s+arm'?s[- ]?length|...` |
| `no_master_file` | high | tax.tp.no_master_file | `(?i)(?:no|absent|missing)\s+master\s+file|master\s+file\s+(?:not\s+(?:prepare...` |
| `no_local_file` | high | tax.tp.no_local_file | `(?i)(?:no|absent|missing)\s+local\s+file|local\s+file\s+(?:not\s+(?:prepared|...` |
| `no_cbcr` | high | tax.tp.no_cbcr | `(?i)country[- ]?by[- ]?country\s+report(?:ing)?\s+(?:not\s+(?:prepared|filed)...` |
| `hard_to_value_intangible` | high | tax.tp.htvi | `(?i)(?:hard[- ]?to[- ]?value\s+intangible|htvi)(?!.{0,300}(?:ex[- ]?post\s+ad...` |
| `cca_no_balancing_payment` | medium | tax.tp.cca_imbalanced | `(?i)cost\s+contribution\s+arrangement\s+(?:without\s+balancing\s+payment|imba...` |
| `pillar_two_etr_below_15` | critical | tax.pillar_two.etr_below_15 | `(?i)(?:effective\s+tax\s+rate|etr)\s+(?:below|under)\s+15\s*%(?!.{0,200}(?:su...` |
| `permanent_establishment_risk` | high | tax.tp.pe_risk | `(?i)(?:dependent\s+agent|fixed\s+place\s+of\s+business|home[- ]?office\s+pe)\...` |
| `fin_tx_no_credit_rating` | medium | tax.tp.fin_tx_no_rating | `(?i)(?:intercompany|related[- ]?party)\s+(?:loan|guarantee|credit\s+facility)...` |

