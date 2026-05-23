# Data cleaning + entity enrichment harness

*harness* · `harness/data-cleaning-and-enrichment` · v0.1.0 · beta

Cross-vertical harness that normalizes a raw customer / vendor /
applicant record: addresses → USPS standardized + geocoded;
phones → E.164; names → canonical with given/family split;
countries → ISO 3166 codes; dates → ISO 8601; emails →
deliverable check; entities → linked to OpenCorporates /
Companies House. Output is a clean, enrichable record ready for
downstream pipelines (ESG / AML / claims / benefits / etc.).

Strictly local-first; external tool calls (USPS / Google Geocode /
OpenCorporates) opt-in via env-var keys.

| axis | value |
|---|---|
| industry | cross_industry, retail, finance, healthcare, government, insurance |
| capability | format_conversion, verification, extraction, anonymization |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `tool_definition`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/customer-record-enrichment`, `pipeline/full-vendor-due-diligence`, `pipeline/benefits-adjudication-review`, `pipeline/insurance-claim-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `no_model` | `none` | local | False | True |
| `local_ollama_fallback` | `ollama` | local | False | False |

## Logic paths

### raw record → standardized + enriched record  
*model_call: `optional`*

1. parse address → USPS standardized + libpostal fallback
1. normalize phones → E.164 (libphonenumber)
1. canonicalize names → given_name + family_name + middle + suffix + honorific
1. resolve countries → ISO 3166 alpha-2/alpha-3/numeric
1. parse dates → ISO 8601
1. validate USPS deliverable (if US + tool/usps-address-validator configured)
1. geocode (if tool/google-geocode configured)
1. entity-link to OpenCorporates (if vendor / B2B record + tool/opencorporates-lookup configured)
1. validate SWIFT BIC (if payment / bank record)
1. compute dedup key for entity resolution

**consumes:** `grep_rule`, `tool_definition`

**emits:** `reasoning_step`, `context_snippet`

**verification:** every field has provenance (source step + confidence), no PII synthesis (e.g. don't FILL IN missing SSN), external-tool calls audited per record



## Privacy boundaries

- **raw_input**: stays local; external tool calls send sanitized fields only
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: USPS / Google Geocode / OpenCorporates / SWIFT BIC — only when their env keys are set AND user opted in

