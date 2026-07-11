# M&A Integration Risk review pipeline

*pipeline* · `pipeline/mna-integration-risk-review` · v0.1.0 · experimental

Benchmarkable m&a integration risk review pipeline with normalization, grep, RAG, harness review, severity calibration, evidence gaps, and risk-register output.

| axis | value |
|---|---|
| industry | m_and_a.integration, m_and_a.due_diligence |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review integration planning packets for Day 1 readiness, TSA dependencies, system migration, controls, and synergy risk.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-mna-integration-risk-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/rag-mna-integration-risk-retrieval-policy` | - |
| 6 | `control_matrix` | processor | `processor/control-matrix-builder` | - |
| 7 | `review_harness` | harness | `harness/mna-integration-risk-review` | - |
| 8 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 11 | `route_owners` | processor | `processor/remediation-owner-router` | - |
| 12 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 13 | `grade` | processor | `processor/llm-judge` | - |
| 14 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 15 | `risk_register` | processor | `processor/risk-register-updater` | - |
| 16 | `summary` | processor | `processor/review-summary-composer` | - |

