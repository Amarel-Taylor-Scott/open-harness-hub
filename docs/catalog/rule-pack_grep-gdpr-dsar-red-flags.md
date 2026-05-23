# GDPR DSAR red-flag detectors

*rule-pack* · `rule-pack/grep-gdpr-dsar-red-flags` · v0.1.0 · beta

GREP detectors for GDPR Data Subject Access Request handling
red flags: missing identity verification, missing-lawful-basis,
unlawful erasure refusal, missing transfer safeguards, missing
breach-notification trace, dark-pattern consent.

| axis | value |
|---|---|
| industry | privacy, privacy.gdpr, privacy.dsar, compliance |
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
| `missing_identity_verification` | critical | gdpr.dsar.no_id_verification | `(?i)(?:no|absent|skipped|not performed)\s+identity\s+verification|identity\s+...` |
| `missing_lawful_basis` | critical | gdpr.lawful_basis.missing | `(?i)(?:no|absent)\s+lawful\s+basis(?:\s+identified)?|lawful\s+basis\s*[:=]\s*...` |
| `deadline_missed` | high | gdpr.dsar.deadline_missed | `(?i)dsar\s+(?:response|fulfillment)\s+(?:delayed|missed\s+deadline|past\s+(?:...` |
| `unlawful_charge` | high | gdpr.dsar.unlawful_charge | `(?i)dsar\s+(?:fee|charge)\s*[:=]\s*\$?[\d.,]+|charged\s+(?:the\s+)?(?:subject...` |
| `special_category_without_basis` | critical | gdpr.special_category.no_basis | `(?i)(?:processing|collected|stored)\s+(?:health|biometric|genetic|racial|ethn...` |
| `transfer_without_safeguard` | high | gdpr.transfer.no_safeguard | `(?i)transfer\s+(?:to|outside)\s+(?:eu|eea)(?!.{0,400}(?:scc|sccs|standard\s+c...` |
| `breach_notification_late` | high | gdpr.breach.notification_late | `(?i)breach\s+notification\s+(?:delayed|over\s+72\s*hours|past\s+72\s*hours|ou...` |
| `dark_pattern_consent` | high | gdpr.consent.dark_pattern | `(?i)(pre[- ]?ticked|pre[- ]?selected)\s+(?:consent|opt[- ]?in)|consent\s+bund...` |
| `no_dpo_appointed` | medium | gdpr.dpo.not_appointed | `(?i)(?:no|absent)\s+(?:dpo|data\s+protection\s+officer)\s+appointed|dpo\s*[:=...` |
| `erasure_refused_without_basis` | high | gdpr.erasure.refusal_without_basis | `(?i)erasure\s+(?:request\s+)?(?:refused|denied)(?!.{0,400}(?:art\.?\s*17\(3\)...` |
| `missing_dpia` | medium | gdpr.dpia.missing | `(?i)(?:no|absent|not\s+performed)\s+dpia(?!.{0,300}(?:not\s+required|low\s+ri...` |
| `automated_decision_no_disclosure` | medium | gdpr.automated_decision.no_disclosure | `(?i)automated\s+decision[- ]?making(?!.{0,400}(?:logic|significance|consequen...` |

