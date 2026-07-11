# Cross-border VAT-ID checksum + reverse-charge applicability validation

*pipeline* · `pipeline/vat-id-checksum-reverse-charge-validation` · v0.1.0 · experimental

Negative-space task: deciding whether an intra-EU B2B invoice was correctly
issued under the VAT reverse-charge mechanism is a deterministic rule the
model gets wrong because it (a) cannot reliably run the per-country VAT-ID
checksum (each member state has its own check-digit algorithm), (b)
hallucinates whether a reverse-charge note is required, and (c) cannot keep
a country's standard VAT rate straight across a long context. This pipeline
pins the supplier/customer VAT-IDs to a deterministic format+checksum check,
retrieves the controlling reverse-charge criteria from a governed corpus,
and verifies the invoice carries the mandatory "reverse charge" wording when
the conditions hold — refusing to bless an invoice that fails the formal
test rather than fluently approving it.

Capability lift is structural: VAT-ID checksums and the reverse-charge
decision are formal rules with a single correct answer, and a deterministic
checker beats a stochastic model on them by construction — the lift survives
model upgrades and costs no model tokens.

Bundle: High-precision regulated RAG (taxonomy Bundle B) — exact-id +
field-weighted retrieval over the VAT framework corpus, cite-or-abstain
output, and deterministic post-call verification gates.

| axis | value |
|---|---|
| industry | tax.indirect, finance.fraud, procurement.contracting |
| capability | verification, extraction, evaluation, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given an intra-EU B2B invoice (digital or scanned), extract supplier and
customer VAT identification numbers, country codes, place-of-supply, and the
presence/absence of a reverse-charge note; deterministically validate each
VAT-ID's national checksum; retrieve the controlling reverse-charge criteria;
and emit a verdict (reverse_charge_correct | missing_reverse_charge_note |
invalid_vat_id | not_reverse_charge) with the cited criterion and the exact
VAT-ID(s) that failed.

**pipeline_kind:** `verify_data`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_countries` | processor | `processor/iso-country-normalize` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-tax-vat-invoice-audit-flags` | - |
| 5 | `retrieve_criteria` | rule_pack | `rule-pack/rag-tax-vat-invoice-audit-retrieval-policy` | - |
| 6 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 7 | `vat_control_matrix` | processor | `processor/control-matrix-builder` | - |
| 8 | `review_harness` | harness | `harness/tax-vat-invoice-audit-review` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 11 | `verify_vat_checksums` | processor | `processor/verify-deterministic-criterion` | - |
| 12 | `grade` | processor | `processor/llm-judge` | - |
| 13 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 14 | `summary` | processor | `processor/review-summary-composer` | - |

