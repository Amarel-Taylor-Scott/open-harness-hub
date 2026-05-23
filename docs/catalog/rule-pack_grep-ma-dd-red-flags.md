# M&A DD red-flag detectors (6 streams)

*rule-pack* · `rule-pack/grep-ma-dd-red-flags` · v0.1.0 · beta

GREP detectors for financial/legal/IP/customer/HR/tax DD.

| axis | value |
|---|---|
| industry | m_and_a, m_and_a.due_diligence, legal, finance |
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
| `change_of_control_acceleration` | critical | ma.legal.cof_acceleration | `(?i)change[- ]?of[- ]?control\s+(?:acceleration|trigger|provision|clause)` |
| `customer_concentration` | high | ma.customer.concentration | `(?i)customer\s+concentration\s*[:=]?\s*[2-9][0-9]%|single\s+customer\s+(?:>|o...` |
| `non_assignable_customer_contract` | high | ma.customer.non_assignable | `(?i)(?:customer|key)\s+contract\s+(?:not\s+assignable|non[- ]?assignable|requ...` |
| `open_ip_litigation` | critical | ma.ip.open_litigation | `(?i)open\s+(?:ip|patent|trademark|copyright)\s+(?:litigation|lawsuit|infringe...` |
| `open_source_gpl_in_proprietary` | high | ma.ip.copyleft_in_proprietary | `(?i)(?:gpl|agpl|lgpl|copyleft)\s+(?:license|code|library)\s+(?:in|incorporate...` |
| `undisclosed_tax_liability` | critical | ma.tax.undisclosed_liability | `(?i)(?:undisclosed|unrecorded)\s+(?:tax|sales\s+tax|use\s+tax|payroll\s+tax)\...` |
| `nol_section_382_limit` | medium | ma.tax.nol_382 | `(?i)(?:nol|net\s+operating\s+loss)\s+limited\s+by\s+(?:section|§|sec\.?)\s*38...` |
| `key_person_no_retention` | high | ma.hr.key_person_attrition | `(?i)key\s+(?:person|employee|founder|cto|ceo|cfo)(?:\s+is)?\s+(?:not\s+(?:ret...` |
| `equity_overhang_high` | medium | ma.hr.equity_overhang | `(?i)equity\s+overhang\s+(?:>|over)\s+(?:1[5-9]|[2-9][0-9])%|unvested\s+(?:opt...` |
| `accrued_pto_undisclosed` | medium | ma.hr.accrued_pto | `(?i)accrued\s+(?:pto|vacation|holiday)\s+(?:liability\s+)?(?:not\s+(?:on\s+ba...` |
| `warn_act_exposure` | high | ma.hr.warn_exposure | `(?i)\bwarn\s+act\b\s+(?:exposure|noncompliance|violation)|mass\s+layoff\s+wit...` |
| `regulatory_enforcement_action` | critical | ma.legal.regulatory_enforcement | `(?i)(?:open|pending|active)\s+(?:sec|fda|ftc|cftc|finra|cma|cnpd|ico|dpa)\s+(...` |
| `going_concern_qualification` | critical | ma.financial.going_concern | `(?i)going[- ]?concern\s+(?:qualification|doubt|opinion)|auditor.{0,40}going[-...` |
| `working_capital_off_target` | medium | ma.financial.working_capital | `(?i)working\s+capital\s+(?:below|under|short\s+of)\s+(?:target|peg)\s+by\s+\$...` |
| `ebitda_adjustment_aggressive` | medium | ma.financial.ebitda_adjustment | `(?i)(?:add[- ]?back|adjustment)\s+(?:to|from)\s+ebitda\s+(?:>|over)\s+(?:1[5-...` |

