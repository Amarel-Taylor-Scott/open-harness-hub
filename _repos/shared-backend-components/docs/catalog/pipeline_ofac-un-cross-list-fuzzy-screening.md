# OFAC / UN cross-list sanctions screening with fuzzy match

*pipeline* · `pipeline/ofac-un-cross-list-fuzzy-screening` · v0.1.0 · experimental

Screen a counterparty (person or entity) name against multiple
sanctions lists at once — OFAC SDN, UN Consolidated, EU Consolidated,
and an institution PEP list — using deterministic fuzzy matching
(name canonicalization + Jaro-Winkler ≥ threshold) so that
transliteration, honorific, and word-order variants are caught, and
every hit carries its source list, program, and listing date.

Negative space: a bare model cannot answer "is NAME on a sanctions
list" — it hallucinates list membership, cannot apply a calibrated
fuzz threshold, and gives no provenance. Screening MUST be a
deterministic match against a governed list snapshot, with the model
used only to summarize and explain matches (cite-or-abstain), never
to decide membership. Cross-list reconciliation flags a name that
hits one list but not another (a coverage gap), and clusters
near-duplicate hits across lists so an analyst sees one entity, not
four rows.

Reference / educational only — list contents are governed snapshots,
inputs are synthetic. Bundle: High-precision legal / regulated RAG
(exact-id + fuzzy leg; source-precedence; cite-or-abstain).

| axis | value |
|---|---|
| industry | finance, finance.aml, finance.kyc, trade.sanctions |
| capability | verification, safety_gating, extraction, classification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



## Task

Given a counterparty name (and optional aliases), screen it across
OFAC SDN, UN Consolidated, EU Consolidated, and an institution PEP
list with deterministic fuzzy matching; cluster near-duplicate hits
across lists into one entity; flag cross-list coverage gaps; and emit
a yes/no sanctions-hit decision with each hit's source list, program,
listing date, and match score. Halt to escalation on any hit.

**pipeline_kind:** `classify`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `canonicalize_name` | processor | `processor/name-canonicalize` | - |
| 2 | `normalize_country` | processor | `processor/iso-country-normalize` | - |
| 3 | `cross_list_screen` | tool | `tool/sanctions-check` | - |
| 4 | `apply_screening_policy` | rule_pack | `rule-pack/sanctions-screening` | - |
| 5 | `cluster_hits` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 6 | `retrieve_list_shape` | knowledge_pack | `knowledge-pack/sanctions-list-shape` | - |
| 7 | `explain_matches` | harness | `harness/aml-investigation` | - |
| 8 | `check_citations` | processor | `processor/citation-span-checker` | - |
| 9 | `escalate` | processor | `processor/escalate-human-review` | $.steps.cross_list_screen.output.matches != [] |
| 10 | `audit` | processor | `processor/audit-trace-emitter` | - |

