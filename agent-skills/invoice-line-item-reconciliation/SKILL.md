---
name: invoice-line-item-reconciliation
description: 'Given a scanned/photographed or digital invoice, extract every line
  item (description, qty, unit_price, line_discount, line_total) plus header totals
  (subtotal, total_discount, net, vat_rate, vat_amount, grand_total, currency), then
  deterministically verify that every line recomputes and that the document foots
  to its printed grand total within a rounding tolerance. Output: per-line extraction
  + a reconciliation verdict (reconciled | discrepancy) with the exact failing equation(s)
  cited.'
when_to_use: 'Pipeline kind: extract.'
---

# Invoice line-item extraction + deterministic total reconciliation

Negative-space task: a bare VLM/LLM can read an invoice and copy out the
printed grand total, but it cannot reliably RECOMPUTE the arithmetic that
proves the total is internally consistent — line_total = qty × unit_price
(minus line discount), Σ line_totals = subtotal, subtotal − discounts =
net, net × vat_rate = vat_amount, net + vat = grand_total. Models drift on
multi-row sums, silently "agree" with a wrong printed total, and produce a
different answer on re-run. This pipeline forces the model to do ONLY the
extraction (each field tied to its source line/cell), then runs the math
as a DETERMINISTIC verifier outside the model and FAILS the run when the
printed total does not reconcile to the recomputed total within tolerance.

Capability lift is structural: the failure is architectural (token-level
arithmetic over many rows is unreliable and non-reproducible), so a
deterministic reconciliation gate keeps lifting no matter how the model
improves — and it costs zero model tokens.

Bundle: High-precision regulated extraction (taxonomy Bundle B) wired with
an OCR pre-pass for the character-level field accuracy a VLM blurs, a
canonical-schema mapper so heterogeneous invoice layouts become one row
shape, and post-call deterministic verification gates.

## Task

Given a scanned/photographed or digital invoice, extract every line item
(description, qty, unit_price, line_discount, line_total) plus header
totals (subtotal, total_discount, net, vat_rate, vat_amount, grand_total,
currency), then deterministically verify that every line recomputes and
that the document foots to its printed grand total within a rounding
tolerance. Output: per-line extraction + a reconciliation verdict
(reconciled | discrepancy) with the exact failing equation(s) cited.

## Steps

1. **ocr_prepass** — `processor` → `processor/on-device-ocr-prepass`
2. **inject_schema** — `processor` → `processor/inject-output-schema`
3. **extract_fields** — `harness` → `harness/text-safety-review`
4. **coerce_json** — `processor` → `processor/json-schema-repair`
5. **canonicalize_lines** — `processor` → `processor/tabular-schema-canonicalizer`
6. **grep_flags** — `rule_pack` → `rule-pack/grep-procure-to-pay-invoice-audit-flags`
7. **retrieve_context** — `rule_pack` → `rule-pack/rag-procure-to-pay-invoice-audit-retrieval-policy`
8. **build_reconciliation_matrix** — `processor` → `processor/control-matrix-builder`
9. **verify_foots_to_total** — `processor` → `processor/verify-deterministic-criterion`
10. **escalate_on_discrepancy** — `processor` → `processor/escalate-human-review` (when `$.steps.verify_foots_to_total.output.pass == false`)
11. **summary** — `processor` → `processor/review-summary-composer`
12. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/invoice-audit-reviewer
- **model_adapter**: adapter/gemma-4-26b-vision
- **knowledge_packs**: `knowledge-pack/procure-to-pay-invoice-audit-frameworks`
- **rule_packs**: `rule-pack/grep-procure-to-pay-invoice-audit-flags`, `rule-pack/rag-procure-to-pay-invoice-audit-retrieval-policy`

## Success criteria

- deterministic `$.steps.verify_foots_to_total.output.pass` == `True`
- deterministic `$.steps.canonicalize_lines.output.unmapped_columns` is_falsy `None`
- rubric `rubric/procure-to-pay-invoice-audit-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/invoice-line-item-reconciliation` v0.1.0
- License: `MIT`
- Industry: procurement.contracting, finance.fraud, tax.indirect
- Full source manifest: see `references/manifest.yaml`
