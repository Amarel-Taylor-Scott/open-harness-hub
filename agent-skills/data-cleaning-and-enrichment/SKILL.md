---
name: data-cleaning-and-enrichment
description: 'Cross-vertical harness that normalizes a raw customer / vendor / applicant
  record: addresses → USPS standardized + geocoded; phones → E.164; names → canonical
  with given/family split; countries → ISO 3166 codes; dates → ISO 8601; emails →
  deliverable check; entities → linked to OpenCorporates / Companies House. Output
  is a clean, enrichable record ready for downstream pipelines (ESG / AML / claims
  / benefits / etc.). Strictly local-first; external tool calls (USPS / Google Geocode
  / OpenCorporates) opt-in via env-var keys.'
when_to_use: Use when the user needs format_conversion. Use when the user needs verification.
  Use when the user needs extraction. Use when the user needs anonymization. Particularly
  relevant for retail. Particularly relevant for finance. Particularly relevant for
  healthcare. Particularly relevant for government. Particularly relevant for insurance.
---

# Data cleaning + entity enrichment harness

Cross-vertical harness that normalizes a raw customer / vendor /
applicant record: addresses → USPS standardized + geocoded;
phones → E.164; names → canonical with given/family split;
countries → ISO 3166 codes; dates → ISO 8601; emails →
deliverable check; entities → linked to OpenCorporates /
Companies House. Output is a clean, enrichable record ready for
downstream pipelines (ESG / AML / claims / benefits / etc.).

Strictly local-first; external tool calls (USPS / Google Geocode /
OpenCorporates) opt-in via env-var keys.

## Applied layers

- `grep`
- `tools`

## raw record → standardized + enriched record

*model_call:* `optional`

**Steps**

1. parse address → USPS standardized + libpostal fallback
2. normalize phones → E.164 (libphonenumber)
3. canonicalize names → given_name + family_name + middle + suffix + honorific
4. resolve countries → ISO 3166 alpha-2/alpha-3/numeric
5. parse dates → ISO 8601
6. validate USPS deliverable (if US + tool/usps-address-validator configured)
7. geocode (if tool/google-geocode configured)
8. entity-link to OpenCorporates (if vendor / B2B record + tool/opencorporates-lookup configured)
9. validate SWIFT BIC (if payment / bank record)
10. compute dedup key for entity resolution

**Verification**

- every field has provenance (source step + confidence)
- no PII synthesis (e.g. don't FILL IN missing SSN)
- external-tool calls audited per record

## Privacy boundaries

- **raw_input**: stays local; external tool calls send sanitized fields only
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: USPS / Google Geocode / OpenCorporates / SWIFT BIC — only when their env keys are set AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `no_model` | `none` | local | False | True |
| `local_ollama_fallback` | `ollama` | local | False | False |

## Provenance

- Hub component: `harness/data-cleaning-and-enrichment` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
