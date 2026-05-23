# Customer record enrichment (deterministic, cross-vertical)

*pipeline* · `pipeline/customer-record-enrichment` · v0.1.0 · beta

Normalize + enrich a raw customer / vendor record. Chains the
format-convert processors (address / phone / name / country /
date) followed by deduplication via entity-resolution-link, with
optional external-tool calls (USPS / geocode / OpenCorporates /
SWIFT BIC) gated on env keys.

| axis | value |
|---|---|
| industry | cross_industry, retail, finance, compliance |
| capability | format_conversion, verification, extraction |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | mixed |
| license | MIT |



## Task

Normalize + enrich + dedupe-key a customer record.

**pipeline_kind:** `enrichment`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `parse_address` | processor | `processor/address-parse-standardize` | — |
| 2 | `normalize_country` | processor | `processor/iso-country-normalize` | — |
| 3 | `normalize_phone` | processor | `processor/phone-normalize-e164` | — |
| 4 | `canonicalize_name` | processor | `processor/name-canonicalize` | — |
| 5 | `parse_dates` | processor | `processor/date-parse-multiformat` | — |
| 6 | `redact_pii` | processor | `processor/redact-pii-text` | — |
| 7 | `audit` | processor | `processor/audit-trace-emitter` | — |

