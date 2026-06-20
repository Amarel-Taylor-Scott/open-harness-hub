# Crypto Exchange Transaction Monitoring review pipeline

*pipeline* · `pipeline/crypto-exchange-transaction-monitoring-review` · v0.1.0 · experimental

Expanded crypto exchange transaction monitoring review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

| axis | value |
|---|---|
| industry | finance.aml, tax.crypto |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review crypto alerts for typology, wallet attribution, sanctions exposure, and SAR/STR escalation.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-crypto-exchange-transaction-monitoring-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/rag-crypto-exchange-transaction-monitoring-retrieval-policy` | - |
| 6 | `review_harness` | harness | `harness/crypto-exchange-transaction-monitoring-review` | - |
| 7 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 8 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 9 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 10 | `grade` | processor | `processor/llm-judge` | - |
| 11 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 12 | `risk_register` | processor | `processor/risk-register-updater` | - |
| 13 | `audit` | processor | `processor/audit-trace-emitter` | - |

