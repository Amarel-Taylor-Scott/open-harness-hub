# Building-permit amendment / regularization router (PH·ID·NG)

*pipeline* · `pipeline/building-permit-amendment-regularization-route` · v0.1.0 · experimental

Detect when reported as-built construction has materially deviated from the
approved building permit such that a revised/amended permit (a regularization
path) is legally required, then route the case to the jurisdiction-specific
authority with citations. Material-alteration definitions, the
added-story/added-use trigger, and the regularization workflow are
jurisdiction-specific and thinly represented online — exactly the
low-digitization valley the national permit/occupancy corpus targets. The
pattern generalizes across PH (PD 1096 / LGU OBO), Indonesia (PBG via SIMBG,
PP 16/2021), and Nigeria (state building-control agencies, e.g. LASBCA);
only the corpus and routing targets change — the deviation logic and the
abstain gate are reusable.

Agentic / corrective-RAG bundle (Bundle D): a two-time retrieval refines the
query from "is this a material alteration?" toward the controlling clause,
official-source verification grades the retrieval, and a corrective human
escalation fires when the retrieval is weak or the approved scope is not
human-verified (tier-4 OBO/PUPR/state record). The router NEVER infers the
approved scope from the model; an unverifiable approved scope yields
PERMIT_RECORD_UNVERIFIABLE. Detection + routing + citations only; no PII; no
guidance on avoiding permits or inspection.

| axis | value |
|---|---|
| industry | construction.permitting, government.permitting, infrastructure |
| capability | extraction, retrieval, verification, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



## Task

Given a building case packet, detect whether the reported as-built deviates from the approved permit enough to require a revised/amended permit (regularization), and route the case to the jurisdiction-specific authority (PH OBO/DPWH, ID Dinas PUPR/SIMBG, NG state building-control) with citations; abstain to a human when the approved scope is not human-verified or retrieval is weak.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `injection_gate` | processor | `processor/prompt-injection-detector` | - |
| 4 | `normalize_evidence` | processor | `processor/packet-evidence-normalizer` | - |
| 5 | `grep_flags` | rule_pack | `rule-pack/grep-municipal-permit-review-flags` | - |
| 6 | `retrieve_material_alteration` | processor | `processor/two-time-retrieval` | - |
| 7 | `verify_sources` | processor | `processor/official-sources-checker` | - |
| 8 | `decide_harness` | harness | `harness/municipal-permit-review-review` | - |
| 9 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 10 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 11 | `route_owner` | processor | `processor/remediation-owner-router` | - |
| 12 | `escalate_human` | processor | `processor/escalate-human-review` | - |
| 13 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 14 | `grade` | processor | `processor/llm-judge` | - |
| 15 | `audit` | processor | `processor/audit-trace-emitter` | - |

