# Solid Waste Route Safety review pipeline

*pipeline* · `pipeline/solid-waste-route-safety-review` · v0.1.0 · experimental

Benchmarkable solid waste route safety review pipeline with normalization, grep, RAG, control matrix, severity calibration, citation checks, and summary output.

| axis | value |
|---|---|
| industry | waste.generator, transportation.trucking |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review solid waste route safety packets for collisions, backing events, contamination, route risk, and corrective action.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-solid-waste-route-safety-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/rag-solid-waste-route-safety-retrieval-policy` | - |
| 6 | `control_matrix` | processor | `processor/control-matrix-builder` | - |
| 7 | `review_harness` | harness | `harness/solid-waste-route-safety-review` | - |
| 8 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 11 | `route_owners` | processor | `processor/remediation-owner-router` | - |
| 12 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 13 | `grade` | processor | `processor/llm-judge` | - |
| 14 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 15 | `summary` | processor | `processor/review-summary-composer` | - |

