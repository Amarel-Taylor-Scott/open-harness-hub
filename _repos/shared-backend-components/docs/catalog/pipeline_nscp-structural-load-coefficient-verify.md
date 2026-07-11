# NSCP / ASCE 7 structural load-coefficient verifier

*pipeline* · `pipeline/nscp-structural-load-coefficient-verify` · v0.1.0 · experimental

Verify the edition-specific numeric coefficients in a structural design
submittal (load-combination equations, importance / seismic-zone factors,
strength-reduction phi factors, allowable-stress increases) against an
authoritative constants corpus rather than the model's memory. Base models
confidently misquote these life-safety numbers because they blend
ASCE 7 / AISC 360 / ACI 318 / Eurocode / NSCP editions — a confident-wrong
failure that is deterministically checkable against the published tables.

This is a Cheap exact-id / keyword-first bundle (Bundle C) with a verify
spine: the structural-design-code-constants Knowledge Corpus is queried by
exact_id (e.g. "ASCE 7-22 load combo 2", "ACI 318 phi flexure", "NSCP 2015
seismic zone 4 Z"), every cited coefficient is checked for citation
coverage, and a deterministic gate requires that the submittal's numbers
match the edition the design claims. The pipeline does NOT perform the
structural-adequacy assessment itself — that is a tier-5 licensed-engineer
on-site act; it flags coefficient mismatches and routes them. Detection and
citation only; no PII.

| axis | value |
|---|---|
| industry | construction.permitting, infrastructure, manufacturing |
| capability | extraction, retrieval, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



## Task

Verify the edition-specific load-combination equations and load / phi / seismic-zone coefficients cited in a structural design submittal against the authoritative structural-design-code-constants corpus, by exact-id lookup, and flag any coefficient that does not match the claimed code edition — with a citation to the published table.

**pipeline_kind:** `verify_data`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `injection_gate` | processor | `processor/prompt-injection-detector` | - |
| 3 | `grep_flags` | rule_pack | `rule-pack/grep-building-code-inspection-flags` | - |
| 4 | `lookup_constants` | processor | `processor/two-time-retrieval` | - |
| 5 | `verify_sources` | processor | `processor/official-sources-checker` | - |
| 6 | `compare_harness` | harness | `harness/building-code-inspection-review` | - |
| 7 | `dedupe_findings` | processor | `processor/finding-deduplicator` | - |
| 8 | `calibrate_severity` | processor | `processor/severity-calibrator` | - |
| 9 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 10 | `grade` | processor | `processor/llm-judge` | - |
| 11 | `audit` | processor | `processor/audit-trace-emitter` | - |

