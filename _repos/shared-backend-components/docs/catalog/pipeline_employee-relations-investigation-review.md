# Employee Relations Investigation review pipeline

*pipeline* · `pipeline/employee-relations-investigation-review` · v0.1.0 · experimental

Benchmarkable employee relations investigation review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

| axis | value |
|---|---|
| industry | hr.performance, hr.hiring |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review employee relations packets for allegation scope, witness evidence, retaliation risk, confidentiality, and remediation.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-employee-relations-investigation-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/rag-employee-relations-investigation-retrieval-policy` | - |
| 6 | `control_matrix` | processor | `processor/control-matrix-builder` | - |
| 7 | `review_harness` | harness | `harness/employee-relations-investigation-review` | - |
| 8 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 11 | `route_owners` | processor | `processor/remediation-owner-router` | - |
| 12 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 13 | `grade` | processor | `processor/llm-judge` | - |
| 14 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 15 | `summary` | processor | `processor/review-summary-composer` | - |

