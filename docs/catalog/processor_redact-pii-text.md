# Redact PII from text (English-centric, MS Presidio-compatible)

*processor* · `processor/redact-pii-text` · v0.1.0 · stable

Strip PII from free-form text before downstream LLM calls or
hub sharing. Detects: email, phone, IBAN, SSN, passport,
national-ID, full names (NER), street addresses, dates of birth,
medical record numbers, and the 18 HIPAA Safe Harbor identifiers.

Drop-in replacement for raw text in any pipeline whose
`lifecycle_position` ≥ pre_api. Replaces detected entities with
`[REDACTED:<TYPE>]` placeholders; preserves text shape so downstream
parsing still works.

| axis | value |
|---|---|
| industry | cross_industry, healthcare, finance, esg |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



