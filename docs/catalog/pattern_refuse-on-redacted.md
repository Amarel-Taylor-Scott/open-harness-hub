# Refuse-on-redacted (null over hallucination on missing fields)

*pattern* · `pattern/refuse-on-redacted` · v0.1.0 · beta

When an input field is missing, redacted, or unreadable, return
`null` (or its user-language equivalent — 'unknown' / 'невідомо'
/ 'unbekannt') rather than hallucinating a plausible value.
Prevents the most dangerous failure mode in document-extraction
pipelines: confident invented numbers, dates, names that the user
treats as authoritative because the model returned them.

Bill_info AI achieves 100% refusal accuracy on 7 redacted documents
in its 28-document eval set. The pattern requires: explicit
schema-level support for null on every field; system prompt with
anti-hallucination instructions; downstream UI that renders null
as a user-language "unknown" rather than as zero or empty string
(which would look like a real value).

Published in Sviatoslav Grabovsky's Bill_info AI (Gemma 4 Good
Hackathon, Impact Track — Digital Equity & Inclusivity).

| axis | value |
|---|---|
| industry | ai, cross_industry, bureaucracy_translation, healthcare, finance |
| capability | safety_gating, verification, extraction |
| modality | text, image |
| lifecycle | beta |
| trust_boundary | local |
| license | CC-BY-4.0 |



