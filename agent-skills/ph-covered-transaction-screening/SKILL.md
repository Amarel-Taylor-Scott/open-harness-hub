---
name: ph-covered-transaction-screening
description: 'Given one PH transaction (amount in PHP, channel, customer profile,
  counterparty), determine: (1) is it a covered transaction by the applicable cash
  threshold; (2) does it match an enumerated suspicious circumstance; (3) is a CTR
  and/or STR due and by when — emitting a yes/no decision with cited threshold and
  indicator references. Halt to human review on any sanctions hit or high-severity
  indicator.'
when_to_use: 'Pipeline kind: classify.'
---

# PH AMLA covered / suspicious transaction screening

Decide whether a single Philippine financial transaction is a COVERED
transaction (cash threshold) and/or a SUSPICIOUS transaction under the
Anti-Money Laundering Act (RA 9160 as amended by RA 10365 / 10927 /
11521), and whether a covered/suspicious-transaction report (CTR/STR)
is due — and within what reporting window — without filing anything.

Negative space: a bare model cannot reliably state the PH covered-
transaction cash threshold, the casino threshold, the reporting window
to AMLC, or which suspicious indicators are enumerated in the law —
it confabulates US-style $10,000 CTR rules. The threshold facts and
the enumerated suspicious-circumstance indicators live in a governed,
dated Knowledge Corpus; the threshold comparison is a deterministic
Conditional, not a model guess. Output is a decision plus the cited
indicators and the reporting window, halted to human review if a
sanctions hit or a high-severity suspicious indicator fires.

Reference / educational only — synthetic transaction inputs; not a
filing engine and not legal advice. Bundle: High-precision legal /
regulated RAG (Bundle B) over a governed AML corpus.

## Task

Given one PH transaction (amount in PHP, channel, customer profile,
counterparty), determine: (1) is it a covered transaction by the
applicable cash threshold; (2) does it match an enumerated suspicious
circumstance; (3) is a CTR and/or STR due and by when — emitting a
yes/no decision with cited threshold and indicator references. Halt
to human review on any sanctions hit or high-severity indicator.

## Steps

1. **redact_pii** — `harness` → `harness/redact-pii-text`
2. **normalize_country** — `processor` → `processor/iso-country-normalize`
3. **canonicalize_customer** — `processor` → `processor/name-canonicalize`
4. **sanctions_screen** — `tool` → `tool/sanctions-check`
5. **retrieve_indicators** — `knowledge_pack` → `knowledge-pack/aml-red-flags-extended`
6. **retrieve_corridor_risk** — `knowledge_pack` → `knowledge-pack/high-risk-corridors-and-sectors`
7. **typology_score** — `rule_pack` → `rule-pack/aml-typologies-fatf`
8. **determine** — `harness` → `harness/aml-investigation`
9. **check_citations** — `processor` → `processor/citation-span-checker`
10. **escalate** — `processor` → `processor/escalate-human-review` (when `$.steps.sanctions_screen.output.matches != [] || $.steps.typology_score.output.max_severity == 'high'`)
11. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/aml-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/aml-red-flags-extended`, `knowledge-pack/high-risk-corridors-and-sectors`
- **rule_packs**: `rule-pack/financial-pii-en`, `rule-pack/sanctions-screening`, `rule-pack/aml-typologies-fatf`

## Success criteria

- rubric `rubric/aml-investigation-v1` threshold 0.8
- deterministic `$.steps.check_citations.output.result.pass` == `True`
- deterministic `$.outputs.is_covered_transaction` in `[True, False]`

## Provenance

- Hub component: `pipeline/ph-covered-transaction-screening` v0.1.0
- License: `MIT`
- Industry: finance, finance.aml, finance.kyc
- Full source manifest: see `references/manifest.yaml`
