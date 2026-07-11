---
name: labor-broker-fee-structure-screen
description: Extract the cost lines from a recruitment / labour-broker contract and
  score each against the IRIS Employer-Pays Principle (employer-borne | worker-borne
  | unclear), citing the contract clause and the fair-recruitment standard.
when_to_use: 'Pipeline kind: extract.'
---

# Labour-broker fee-structure screen (IRIS Employer-Pays Principle)

HIGH-PRECISION migrant-worker-protection pipeline. Reads a recruitment
agreement / labour-broker MOU / manpower-supply contract and extracts its
fee-and-cost structure, then scores it against the IRIS "Employer Pays
Principle" and the ILO general principles on fair recruitment: who bears
recruitment fees and related costs (visa, medical, travel, training,
document processing), and whether any cost is passed to — or recovered
from — the worker via deduction.

Negative-space task: recruitment contracts bury cost-allocation across
fee schedules, deduction clauses, "service charges", and side letters, in
multiple currencies, often with euphemisms ("mobilisation cost",
"processing charge recoverable from salary"). A bare model summarising the
contract cannot reliably attribute *each cost line to a payer* and flag the
worker-borne ones — and that attribution is the entire compliance question.
The durable lift is structured, cited cost-line attribution against a fixed
fair-recruitment standard.

Bundle: High-precision legal / regulated RAG (taxonomy Bundle B) — query
decomposition over cost categories, hybrid retrieval against the
due-diligence regulatory pack (ILO/IRIS material), cross-encoder rerank,
a faithful pre-model extraction of every cost line, then a cite-or-abstain
judge that labels each cost line worker-borne / employer-borne / unclear.
Output is a fee-allocation scorecard plus a worker-reimbursement exposure
flag, NOT a legal determination.

## Task

Extract the cost lines from a recruitment / labour-broker contract and score each against the IRIS Employer-Pays Principle (employer-borne | worker-borne | unclear), citing the contract clause and the fair-recruitment standard.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **normalize_country** — `processor` → `processor/iso-country-normalize`
4. **decompose_cost_categories** — `processor` → `processor/sub-question-decomposer`
5. **grep_fee_flags** — `rule_pack` → `rule-pack/grep-apparel-forced-labor-trace-flags`
6. **extract_cost_lines** — `processor` → `processor/faithful-extract-before-model`
7. **retrieve_fair_recruitment** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
8. **rerank_standard** — `processor` → `processor/cross-encoder-reranker`
9. **score_allocation** — `harness` → `harness/apparel-forced-labor-trace-review`
10. **calibrate_severity** — `processor` → `processor/severity-calibrator`
11. **extract_evidence_gaps** — `processor` → `processor/evidence-gap-extractor`
12. **check_citations** — `processor` → `processor/citation-span-checker`
13. **grade** — `processor` → `processor/llm-judge`
14. **redaction_audit** — `processor` → `processor/packet-redaction-audit`
15. **summary** — `processor` → `processor/review-summary-composer`
16. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/esg-auditor
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/csddd-and-forced-labor-indicators`
- **rule_packs**: `rule-pack/grep-apparel-forced-labor-trace-flags`, `rule-pack/hybrid-retrieval-policy`

## Success criteria

- rubric `rubric/apparel-forced-labor-trace-quality-v1` threshold 0.7
- deterministic `$.steps.check_citations.output.result.pass` == `True`
- deterministic `$.steps.redaction_audit.output.result.pass` == `True`

## Provenance

- Hub component: `pipeline/labor-broker-fee-structure-screen` v0.1.0
- License: `MIT`
- Industry: esg.modern_slavery, supply_chain.due_diligence, legal.immigration, humanitarian.trafficking
- Full source manifest: see `references/manifest.yaml`
