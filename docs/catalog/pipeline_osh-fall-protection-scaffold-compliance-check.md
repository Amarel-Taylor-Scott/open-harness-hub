# OSH fall-protection & scaffold compliance check (DO 198 / OSHA 1926)

*pipeline* · `pipeline/osh-fall-protection-scaffold-compliance-check` · v0.1.0 · experimental

Review a construction-site safety packet (job hazard analysis, scaffold
inspection tags, toolbox-talk logs, safety-officer accreditation) for
fall-protection and scaffolding compliance, grounded in the Philippine
Occupational Safety and Health Standards (RA 11058 + DOLE Department Order
198 s. 2018) cross-walked to OSHA 29 CFR 1926 (Subpart L scaffolds, Subpart
M fall protection, Focus Four). It flags: working at height without fall
protection, scaffold erected/used without a competent person, scaffold
defects, and a site at/above the size threshold operating without a
DOLE/PRC-accredited safety officer — then routes worker-safety flags to the
DOLE Regional Office (OSH division) alongside the building-code path.

Standard hybrid RAG bundle (Bundle A) over the OSHA-1926 corpus with a
deterministic grep pre-screen for the Focus-Four signals; the
safety-officer accreditation is an accountability_or_license signal a model
cannot hold, so its absence is flagged and routed, never assumed satisfied.
Detection + routing + citations only; no worker PII stored; no advice on
evading safety requirements.

| axis | value |
|---|---|
| industry | construction, construction.safety, infrastructure |
| capability | evaluation, extraction, verification, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



## Task

Review a construction-site safety packet for fall-protection and scaffolding compliance under RA 11058 / DO 198 (cross-walked to OSHA 1926 Subparts L/M), flag missing fall protection, scaffold-without-competent-person, scaffold defects, and missing accredited safety officer, recommend whether work should stop, and route worker-safety flags to the DOLE Regional Office with citations.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `injection_gate` | processor | `processor/prompt-injection-detector` | - |
| 4 | `grep_red_flags` | rule_pack | `rule-pack/grep-construction-safety-flags` | - |
| 5 | `rag_against_osha` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 6 | `review_harness` | harness | `harness/workplace-safety-incident-review` | - |
| 7 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 8 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 9 | `route_owner` | processor | `processor/remediation-owner-router` | - |
| 10 | `escalate_human` | processor | `processor/escalate-human-review` | - |
| 11 | `grade` | processor | `processor/llm-judge` | - |
| 12 | `audit` | processor | `processor/audit-trace-emitter` | - |

