# Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags

*rule-pack* · `rule-pack/grep-biosecurity-flags` · v0.1.0 · beta

Detectors for 42 CFR 73 / BMBL / WHO LBM4 / DURC compliance gaps.

| axis | value |
|---|---|
| industry | biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc |
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
| `unescorted_access_no_sra` | critical | biosec.access.no_sra | `(?i)(?:without\s+(?:an\s+)?active\s+(?:fbi\s+)?(?:security\s+risk\s+assessmen...` |
| `inventory_variance_form4` | critical | biosec.inventory.variance | `(?i)(?:(?<!no\s)(?<!zero\s)(?:select\s+agent\s+)?inventory\s+(?:mismatch|vari...` |
| `dual_key_breached` | critical | biosec.access.dual_key_breached | `(?i)(?:dual[- ]?key|two[- ]?person)\s+(?:procedure|access|requirement)\s+(?:w...` |
| `gain_of_function_no_durc_p3co` | critical | biosec.durc.no_review | `(?i)(?:gain[- ]?of[- ]?function|aerosol(?:ization)?\s+(?:protocol|experiment)...` |
| `release_loss_unreported_7d` | critical | biosec.release.unreported | `(?i)(?:spill|release|loss|theft)[\s\S]{0,200}?(?:not\s+reported\s+to\s+(?:cdc...` |
| `transfer_form2_missing` | high | biosec.transfer.no_form2 | `(?i)(?:shipped|transferred)[\s\S]{0,200}?(?:without\s+(?:the\s+)?(?:aphis\s*[...` |
| `bsc_certification_overdue` | high | biosec.bsc.cert_overdue | `(?i)(?:bsc[- ]?ii|biosafety\s+cabinet)\s+(?:annual\s+)?(?:recertification|cer...` |
| `hepa_leak_test_overdue` | medium | biosec.hepa.overdue | `(?i)hepa\s+(?:push[- ]?through\s+)?(?:filter\s+)?(?:leak|integrity|pao|dop)\s...` |
| `autoclave_unvalidated_cycle` | high | biosec.decon.unvalidated | `(?i)(?:autoclave|sterilization)\s+(?:short\s+cycle|unvalidated\s+cycle|cycle\...` |
| `ppe_doffing_violation` | medium | biosec.ppe.doffing | `(?i)ppe\s+doffing\s+(?:sequence\s+)?violation|doffing\s+(?:sequence\s+)?(?:vi...` |
| `visitor_log_incomplete` | low | biosec.visitor.log_incomplete | `(?i)visitor\s+log\s+(?:incomplete|gap|missing|not\s+maintained)` |

