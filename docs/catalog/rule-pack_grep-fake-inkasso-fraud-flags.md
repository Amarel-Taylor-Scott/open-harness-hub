# Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)

*rule-pack* · `rule-pack/grep-fake-inkasso-fraud-flags` · v0.1.0 · beta

GREP detectors for the 10 Verbraucherzentrale Fake-Inkasso
indicators. Used by `pipeline/bill-info-extract-fraud-detect-recommend`
as a deterministic FIRST PASS before the LLM-based fraud-detect
call — fires hard-rule indicators that the LLM call then weights
+ classifies.

Sourced from Sviatoslav Grabovsky's Bill_info AI (Bill_info AI on
Hugging Face Spaces) which uses these indicators across both the
Gemma 4 26B fraud-detect call AND a deterministic business_rules
layer.

| axis | value |
|---|---|
| industry | bureaucracy_translation, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee |
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
| `foreign_iban_non_dach` | critical | fake_inkasso.iban.foreign_non_dach | `(?i)\b(?:IBAN[:\s]*)?(?:PL|CZ|SK|LV|LT|EE|HU|RO|BG|HR|SI|GR|MT|CY|TR|UA|RU|BY...` |
| `private_person_recipient` | critical | fake_inkasso.recipient.private_person | `(?i)(?:empfänger|recipient|payee|payment\s+to)[:\s]+(?:herr|frau|mr|mrs|ms)\s...` |
| `legal_threats_first_letter` | critical | fake_inkasso.legal_threats.no_prior_mahnung | `(?i)(?:gerichtsvollzieher|gerichtliche\s+schritte|zwangsvollstreckung|schufa[...` |
| `extreme_deadline_24_72h` | critical | fake_inkasso.deadline.extreme_24_72h | `(?i)(?:zahlungsfrist|frist|deadline|bis\s+spätestens)[:\s]+(?:24|48|72)\s*(?:...` |
| `missing_handelsregister` | medium | fake_inkasso.missing_handelsregister | `(?i)inkasso(?:firma|gmbh|ag|dienst)[\s\S]{0,500}?(?!.{0,400}(?:hrb\s*\d+|hra\...` |
| `unclear_creditor` | medium | fake_inkasso.unclear_creditor | `(?i)(?:gläubiger|creditor|original[- ]?creditor)[:\s]*(?:n[\.\/]?a|unbekannt|...` |
| `dubious_excess_fees` | medium | fake_inkasso.dubious_excess_fees | `(?i)(?:bearbeitungsgebühr|express[- ]?versand|express[- ]?versandkosten|sonde...` |
| `phantom_company_name` | medium | fake_inkasso.phantom_company_name | `(?i)(?:forderungsmanagement|inkassodienst|rechtsabteilung|forderungsstelle|ma...` |
| `premium_phone_number` | medium | fake_inkasso.premium_phone | `(?i)(?:tel(?:efon)?|phone|hotline)[:\s]+(?:0?900\s?\d+|0?180\s?\d+|\+49[- ]?9...` |
| `letzte_mahnung_first_letter` | medium | fake_inkasso.pressure_tactics | `(?i)\bletzte\s+mahnung\b|\bfinal\s+(?:reminder|notice)\b|\bsofortige\s+(?:zah...` |
| `missing_aufsichtsbehoerde` | low | fake_inkasso.missing_aufsichtsbehoerde | `(?i)inkasso[\s\S]{0,500}?(?!.{0,400}aufsichtsbehörde\s+(?:oberlandesgericht|o...` |

