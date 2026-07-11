---
name: id-document-mrz-checkdigit-tamper-verify
description: Given a photo/scan of a passport or ID card's data page, OCR the Machine-Readable
  Zone, parse the document type/issuing-state/document number/birth-date/expiry/optional
  fields, recompute every ICAO 9303 check digit (per-field + composite) deterministically,
  screen the image for tamper indicators (low OCR confidence, font/spacing anomalies,
  expiry in the past), and emit a verdict (mrz_valid | check_digit_failed | tampered
  | expired) with the exact failing field(s) and check digit(s) cited. No biometric
  face match or liveness is performed.
when_to_use: 'Pipeline kind: verify_data.'
---

# ID-document MRZ check-digit verification + tamper-indicator screen

Negative-space task: validating a passport/ID Machine-Readable Zone (MRZ)
has two parts a bare VLM structurally fails. (1) The ICAO 9303 check digits
are a deterministic mod-10 weighted (7-3-1) checksum over each field plus a
composite digit — a model "reads" the MRZ but cannot reliably RECOMPUTE the
checksums, and will happily declare a forged MRZ valid. (2) Tamper screening
needs character-level OCR confidence, font/spacing consistency, and image
metadata signals the VLM's lossy vision tokens cannot see. This pipeline
runs a deterministic OCR pre-pass for the exact MRZ glyphs, recomputes every
ICAO 9303 check digit OUTSIDE the model, screens for tamper indicators, and
refuses to pass a document whose MRZ does not self-verify — instead of
emitting a fluent but ungrounded "looks authentic".

This is an identity-assurance support tool over a SUBMITTED document image;
it does NOT do biometric 1:1 face matching or liveness. Capability lift is
structural: MRZ check digits are a formal checksum (one correct answer) and
a deterministic recomputation beats a stochastic reader by construction; the
lift survives model upgrades and costs no model tokens.

Bundle: High-precision regulated extraction (taxonomy Bundle B) with a
deterministic OCR pre-pass, exact-id/checksum verification, and a tamper
Conditional that halts and routes to human review on any failed indicator.

## Task

Given a photo/scan of a passport or ID card's data page, OCR the
Machine-Readable Zone, parse the document type/issuing-state/document
number/birth-date/expiry/optional fields, recompute every ICAO 9303
check digit (per-field + composite) deterministically, screen the image for
tamper indicators (low OCR confidence, font/spacing anomalies, expiry in the
past), and emit a verdict (mrz_valid | check_digit_failed | tampered |
expired) with the exact failing field(s) and check digit(s) cited. No
biometric face match or liveness is performed.

## Steps

1. **ocr_mrz** — `processor` → `processor/on-device-ocr-prepass`
2. **inject_schema** — `processor` → `processor/inject-output-schema`
3. **parse_mrz_fields** — `harness` → `harness/text-safety-review`
4. **coerce_json** — `processor` → `processor/json-schema-repair`
5. **normalize_dates** — `processor` → `processor/date-parse-multiformat`
6. **grep_flags** — `rule_pack` → `rule-pack/grep-dsar-identity-verification-flags`
7. **retrieve_context** — `rule_pack` → `rule-pack/rag-dsar-identity-verification-retrieval-policy`
8. **build_checkdigit_matrix** — `processor` → `processor/control-matrix-builder`
9. **verify_check_digits** — `processor` → `processor/verify-deterministic-criterion`
10. **verify_not_tampered** — `processor` → `processor/verify-deterministic-criterion`
11. **escalate_on_failure** — `processor` → `processor/escalate-human-review` (when `$.steps.verify_check_digits.output.pass == false || $.steps.verify_not_tampered.output.pass == false`)
12. **summary** — `processor` → `processor/review-summary-composer`
13. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/dsar-identity-reviewer
- **model_adapter**: adapter/gemma-4-26b-vision
- **knowledge_packs**: `knowledge-pack/dsar-identity-verification-frameworks`
- **rule_packs**: `rule-pack/grep-dsar-identity-verification-flags`, `rule-pack/rag-dsar-identity-verification-retrieval-policy`

## Success criteria

- deterministic `$.steps.verify_check_digits.output.pass` == `True`
- deterministic `$.steps.verify_not_tampered.output.pass` == `True`
- rubric `rubric/dsar-identity-verification-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/id-document-mrz-checkdigit-tamper-verify` v0.1.0
- License: `MIT`
- Industry: security.fraud, privacy.dsar, government.benefits
- Full source manifest: see `references/manifest.yaml`
