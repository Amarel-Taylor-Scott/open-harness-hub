# PHI (HIPAA 18-identifier) — English text

*rule-pack* · `rule-pack/phi-hipaa-en` · v0.1.0 · beta

Detection patterns for the 18 HIPAA "Safe Harbor" PHI identifiers in
English text. Designed to feed `harness/redact-pii-text` and any
downstream healthcare pipeline that needs a hard PHI gate before
model or external calls.

This is a baseline; covered entities should layer institution-specific
rules on top.

| axis | value |
|---|---|
| industry | healthcare |
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
| `mrn` | critical | phi.id | `(?i)\b(?:MRN|medical record (?:no\.?|number))\s*:?\s*[A-Z0-9-]{4,}\b` |
| `health_plan_beneficiary` | critical | phi.id | `(?i)\b(?:HPB|HICN|MBI)\s*:?\s*[A-Z0-9-]{6,}\b` |
| `device_id_serial` | high | phi.id | `(?i)\b(?:device (?:id|serial)|implant (?:id|serial))\s*:?\s*[A-Z0-9-]{4,}\b` |
| `biometric_marker` | critical | phi.biometric | `(?i)\b(?:fingerprint|voiceprint|retinal scan)\s*:?` |
| `full_face_photo_ref` | high | phi.biometric | `(?i)\b(?:full[- ]face (?:photo|photograph))` |
| `ssn` | critical | phi.id | `\b\d{3}-\d{2}-\d{4}\b` |
| `phone` | high | phi.contact | `(?i)(?:\+?1[- .]?)?\(?\d{3}\)?[- .]?\d{3}[- .]?\d{4}` |
| `email` | high | phi.contact | `(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` |
| `url` | medium | phi.contact | `(?i)https?://[^\s]+` |
| `ipv4` | medium | phi.contact | `\b(?:\d{1,3}\.){3}\d{1,3}\b` |
| `address_zip_us` | medium | phi.address | `\b\d{5}(?:-\d{4})?\b` |
| `date_full` | medium | phi.date | `\b\d{1,2}/\d{1,2}/\d{4}\b` |
| `age_over_89` | high | phi.demographic | `(?i)\b(9[0-9]|1[0-9]{2})[- ]?(?:year|yr)s?[- ]old\b` |

