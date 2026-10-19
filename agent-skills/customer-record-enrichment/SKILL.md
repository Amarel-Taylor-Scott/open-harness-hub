---
name: customer-record-enrichment
description: Normalize + enrich + dedupe-key a customer record.
when_to_use: 'Pipeline kind: enrichment.'
---

# Customer record enrichment (deterministic, cross-vertical)

Normalize + enrich a raw customer / vendor record. Chains the
format-convert processors (address / phone / name / country /
date) followed by deduplication via entity-resolution-link, with
optional external-tool calls (USPS / geocode / OpenCorporates /
SWIFT BIC) gated on env keys.

## Task

Normalize + enrich + dedupe-key a customer record.

## Steps

1. **parse_address** — `processor` → `processor/address-parse-standardize`
2. **normalize_country** — `processor` → `processor/iso-country-normalize`
3. **normalize_phone** — `processor` → `processor/phone-normalize-e164`
4. **canonicalize_name** — `processor` → `processor/name-canonicalize`
5. **parse_dates** — `processor` → `processor/date-parse-multiformat`
6. **redact_pii** — `processor` → `processor/redact-pii-text`
7. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Success criteria

- deterministic `$.steps.parse_address.output.confidence` > `0`
- deterministic `$.steps.normalize_phone.output.is_valid` is_truthy `None`
- deterministic `$.steps.normalize_country.output.is_valid` is_truthy `None`

## Provenance

- Hub component: `pipeline/customer-record-enrichment` v0.1.0
- License: `MIT`
- Industry: cross_industry, retail, finance, compliance
- Full source manifest: see `references/manifest.yaml`
