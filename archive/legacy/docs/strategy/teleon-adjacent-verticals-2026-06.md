# Teleon adjacent verticals — the adjudication shape, without insurance (2026-06-22)

Owner constraint (non-compete + CLAUDE.md): **stay away from insurance; never expand legacy insurance examples.** So we
target the *structural pattern* of claims-style adjudication — **unstructured intake → extraction → validation →
policy/rules lookup → decision → downstream action** — in document-heavy, policy-heavy, repetitive-decision verticals
that share that shape, and we **pitch the pattern, not a vertical.** Single source: `architecture/adjacent_verticals.json`
(guardrail-checked by `scripts/check_adjacent_verticals.py`). serves_truth=false.

## Why these verticals (the shape is the product)
Each is the same expensive default today — *send the whole document to a frontier model each step* — and the same
Teleon descent applies (OCR + deterministic extraction + rules/policy engine + small model, frontier reserved for the
ambiguous residual). Each maps to an agentic loop we already catalog (`agentic_loop_catalog.json`):

| Vertical | Sector | Maps to loop | Demo |
|---|---|---|---|
| Accounts payable / finance ops | finance | `financial_ops` | invoice processing |
| Loan origination & underwriting | lending | `financial_ops` | loan underwriting |
| Procurement & vendor ops | procurement | `procurement_supply_chain` | procurement workflow |
| Enterprise contract review | legal | `legal_analysis` | contract review |
| Healthcare admin (non-clinical back office) | healthcare_admin | `extraction` | form adjudication |
| Compliance review | compliance | `legal_analysis` | compliance review |
| Customer support resolution | support | `support` | support automation |
| KYC / identity verification | identity | `extraction` | KYC verification |
| Government form processing | government | `extraction` | form processing |
| Enterprise data ingestion | data | `data_engineering` | ingestion pipeline |

(Healthcare = **operational admin only** — no diagnosis/treatment/clinical claims.)

## Positioning (vertical-neutral)
> *"We observe expensive AI-driven enterprise workflows and progressively compile them into optimized, bounded systems
> that cut inference cost by replacing generalized reasoning with specialized execution."*

Category language that avoids any restricted vertical: *complex document-driven operational workflows · policy-intensive
enterprise decision pipelines · high-volume unstructured intake · multi-stage verification & adjudication.* This is the
[[cognitive-compiler]] thesis applied to go-to-market — the same descent, named by pattern not by sector.

## The guardrail (enforced in code)
`check_adjacent_verticals.py` fails if any vertical/demo is insurance (sector/name/pipeline) — so the non-compete rule
can't be violated by a future addition. The only allowed mention of "insurance" is the explicit `avoid` exclusion.

## Flagship demos (already real or queued)
Invoice processing and contract review map directly to the **document-extraction cascade** (the land-lease flagship is
the same shape, in oil & gas / land — *not* insurance). The favorite demo set: invoice · contract · loan-underwriting ·
support · procurement.
