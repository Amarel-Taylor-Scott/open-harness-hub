# Worker-voice ILO 11-indicator extraction (grievance / interview transcripts)

*pipeline* · `pipeline/worker-voice-ilo-indicator-extract` · v0.1.0 · experimental

DEFENSIVE worker-protection pipeline. Reads an *anonymized worker-voice
artifact* — a grievance-line transcript, exit-interview note, or social-
audit worker-interview summary — and extracts which of the ILO 11 forced-
labour indicators are *evidenced* in the worker's own words, returning a
per-indicator present / absent / insufficient-evidence verdict with the
quoted span and the ILO indicator definition for each.

Negative-space task: worker testimony is colloquial, multilingual, and
partial; the same lived experience maps to ILO indicators only through a
fixed definitional frame ("they keep my passport" -> retention of identity
documents; "I owe the agent and work it off" -> debt bondage). A bare model
over-reads — inferring "abuse of vulnerability" or "intimidation" from tone
alone — or under-reads, missing an indicator stated obliquely. The durable
lift is disciplined, cited mapping of testimony spans to the eleven
indicator definitions, with hard abstention where the text does not support
a mapping. Over-attribution in this domain is a safety harm: it can
mislabel a worker's account.

Bundle: Agentic / CRAG (taxonomy Bundle D) — a corrective retrieval gate
grades whether the retrieved ILO indicator definitions actually cover the
testimony before the model maps; if coverage is weak the query is
decomposed and re-retrieved, and the model is held to insufficient-evidence
rather than guessing. `pattern/refuse-on-redacted` enforces abstention on
redacted/missing spans. Output is a cited indicator map for a trained
caseworker / auditor, NOT a victim determination and NOT a referral by
itself.

| axis | value |
|---|---|
| industry | humanitarian.trafficking, esg.modern_slavery, supply_chain.audit, legal.immigration |
| capability | extraction, classification, retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Extract which of the ILO 11 forced-labour indicators are evidenced in an anonymized worker-voice transcript (present | absent | insufficient-evidence), citing the testimony span and the ILO indicator definition, abstaining where unsupported.

**pipeline_kind:** `extract`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_pii` | processor | `processor/redact-pii-text` | - |
| 3 | `grep_indicator_cues` | rule_pack | `rule-pack/grep-human-trafficking-ugc-flags` | - |
| 4 | `decompose_indicators` | processor | `processor/sub-question-decomposer` | - |
| 5 | `retrieve_definitions` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 6 | `grade_retrieval` | processor | `processor/document-grader` | - |
| 7 | `rerank_definitions` | processor | `processor/cross-encoder-reranker` | - |
| 8 | `extract_spans` | processor | `processor/faithful-extract-before-model` | - |
| 9 | `map_indicators` | harness | `harness/apparel-forced-labor-trace-review` | - |
| 10 | `iterate_if_weak` | loop | `pattern/corrective-rag` | $.steps.grade_retrieval.output.result.coverage_weak == true |
| 11 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 12 | `extract_evidence_gaps` | processor | `processor/evidence-gap-extractor` | - |
| 13 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 14 | `grade` | processor | `processor/llm-judge` | - |
| 15 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 16 | `caseworker_handoff` | processor | `processor/escalate-human-review` | - |
| 17 | `summary` | processor | `processor/review-summary-composer` | - |
| 18 | `audit` | processor | `processor/audit-trace-emitter` | - |

