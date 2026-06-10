# School IEP Compliance review pipeline

*pipeline* · `pipeline/school-iep-compliance-review` · v0.1.0 · experimental

Expanded school iep compliance review pipeline with evidence normalization, grep, RAG, harness review, severity calibration, and audit output.

| axis | value |
|---|---|
| industry | education.k12 |
| capability | evaluation, extraction, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Review IEP packets for timelines, services, accommodations, consent, and implementation evidence.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 4 | `grep_flags` | rule_pack | `rule-pack/grep-school-iep-compliance-flags` | - |
| 5 | `retrieve_context` | rule_pack | `rule-pack/rag-school-iep-compliance-retrieval-policy` | - |
| 6 | `review_harness` | harness | `harness/school-iep-compliance-review` | - |
| 7 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 8 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 9 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 10 | `grade` | processor | `processor/llm-judge` | - |
| 11 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 12 | `risk_register` | processor | `processor/risk-register-updater` | - |
| 13 | `audit` | processor | `processor/audit-trace-emitter` | - |

