# Structured JSON → prose normalizer (for GREP-style rule packs)

*processor* · `processor/structured-to-prose` · v0.1.0 · stable

Walk a JSON object and emit one prose-like line per leaf value,
flattening dict keys into space-separated labels. The output shape
is what GREP-family rule packs (regex on natural-language prose)
expect — converting structured supplier disclosures, audit
reports, or KYC packets into a form where pattern detection
works correctly.

Without this step, patterns like `\b(passport)\s+(held|retained)`
miss "passport_location: Held by the workshop" because the
underscore-separated key prevents direct adjacency. The processor
emits `passport location: Held by the workshop` — and the pattern
fires correctly.

Used by `pipeline/supplier-policy-grading` between the PII-
redaction step and the GREP step.

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance, cross_industry |
| capability | format_conversion |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



