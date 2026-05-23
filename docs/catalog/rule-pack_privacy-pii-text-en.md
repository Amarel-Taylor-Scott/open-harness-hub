# Privacy PII (English text)

*rule-pack* · `rule-pack/privacy-pii-text-en` · v0.1.0 · stable

Baseline GREP rule pack for detecting common PII in English text.
Emails, phone numbers, US SSN, passport numbers, IBANs, IPv4. Designed
to feed `harness/redact-pii-text` and any downstream pipeline that
needs a hard PII gate before model or external calls.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `email` | high | pii.contact | `(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` |
| `phone_e164` | medium | pii.contact | `\+?[1-9]\d{1,14}` |
| `us_ssn` | critical | pii.id | `\b\d{3}-\d{2}-\d{4}\b` |
| `passport_generic` | critical | pii.id | `(?i)passport (?:no\.?|number)?\s*:?\s*[A-Z0-9]{6,9}` |
| `iban` | high | pii.financial | `[A-Z]{2}\d{2}[A-Z0-9]{4,30}` |
| `ipv4` | low | pii.network | `\b(?:\d{1,3}\.){3}\d{1,3}\b` |

