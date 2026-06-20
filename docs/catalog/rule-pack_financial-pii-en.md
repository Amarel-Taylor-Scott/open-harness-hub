# Financial PII (English)

*rule-pack* · `rule-pack/financial-pii-en` · v0.1.0 · beta

Detection patterns for common financial PII in English transaction
narratives and KYC documents — account numbers, IBANs, SWIFT/BIC,
card PANs (Luhn-likely), SSN/TIN. Designed to gate any pipeline
that exports beyond the institution's own systems.

| axis | value |
|---|---|
| industry | finance |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `privacy`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `iban` | high | fin.account | `[A-Z]{2}\d{2}[A-Z0-9]{4,30}` |
| `swift_bic` | medium | fin.routing | `\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b` |
| `us_routing_aba` | high | fin.routing | `\b(?:0[0-9]|1[0-2]|2[1-9]|3[0-2])\d{7}\b` |
| `card_pan_luhn_like` | critical | fin.card | `\b(?:\d[ -]?){13,19}\b` |
| `ssn_tin` | critical | fin.tax_id | `\b\d{3}-\d{2}-\d{4}\b` |
| `ein` | high | fin.tax_id | `\b\d{2}-\d{7}\b` |
| `account_no_explicit` | high | fin.account | `(?i)\baccount (?:no\.?|number)\s*:?\s*[A-Z0-9-]{6,}` |

