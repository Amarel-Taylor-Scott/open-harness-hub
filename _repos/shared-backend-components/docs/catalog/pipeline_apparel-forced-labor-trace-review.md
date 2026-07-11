# Apparel Forced Labor Trace review pipeline

*pipeline* · `pipeline/apparel-forced-labor-trace-review` · v0.1.0 · experimental

Benchmarkable apparel forced labor trace review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

| axis | value |
|---|---|
| industry | esg.modern_slavery, supply_chain.due_diligence |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review apparel supplier packets for forced-labor risk, traceability gaps, recruitment fees, and remediation evidence.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-apparel-forced-labor-trace-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/rag-apparel-forced-labor-trace-retrieval-policy` | - |
| 6 | `control_matrix` | processor | `processor/control-matrix-builder` | - |
| 7 | `review_harness` | harness | `harness/apparel-forced-labor-trace-review` | - |
| 8 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 11 | `route_owners` | processor | `processor/remediation-owner-router` | - |
| 12 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 13 | `grade` | processor | `processor/llm-judge` | - |
| 14 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 15 | `risk_register` | processor | `processor/risk-register-updater` | - |
| 16 | `summary` | processor | `processor/review-summary-composer` | - |

