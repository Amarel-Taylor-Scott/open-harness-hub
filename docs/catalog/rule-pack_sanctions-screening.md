# Sanctions screening (deterministic)

*rule-pack* · `rule-pack/sanctions-screening` · v0.1.0 · experimental

Heuristic rule pack for sanctions screening. Each rule is a
condition that pairs a normalized entity name (or fuzzy match) with
a sanctions list and a fuzz threshold. The harness pre-normalizes
the entity (transliterate, fold case, strip honorifics) before
evaluating. Backed by a sanctions-list knowledge pack.

| axis | value |
|---|---|
| industry | finance, finance.aml, finance.kyc |
| capability | safety_gating, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `heuristic`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `ofac_sdn_exact` | critical | — | `fuzzy_match(entity.normalized_name, list='ofac_sdn') >= 1.00` |
| `ofac_sdn_fuzzy` | high | — | `fuzzy_match(entity.normalized_name, list='ofac_sdn') >= 0.92` |
| `un_consolidated_list` | high | — | `fuzzy_match(entity.normalized_name, list='un_consolidated') >= 0.92` |
| `eu_sanctions_list` | high | — | `fuzzy_match(entity.normalized_name, list='eu_consolidated') >= 0.92` |
| `pep_list` | medium | — | `fuzzy_match(entity.normalized_name, list='institution_pep') >= 0.92` |
| `adverse_media_negative` | medium | — | `adverse_media_score(entity.normalized_name) >= 0.75` |

