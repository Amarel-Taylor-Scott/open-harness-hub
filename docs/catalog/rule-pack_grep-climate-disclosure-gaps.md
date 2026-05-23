# Climate disclosure gap detectors (TCFD / ISSB / ESRS E1)

*rule-pack* · `rule-pack/grep-climate-disclosure-gaps` · v0.1.0 · beta

GREP detectors for the highest-leverage climate-disclosure gaps:
missing Scope-3 categories, missing transition plan, board-
oversight silence, no 2C scenario analysis, no SBTi commitment,
missing assurance, market-based-only Scope 2.

| axis | value |
|---|---|
| industry | climate, esg, finance, compliance |
| capability | safety_gating, classification, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `scope_3_not_measured` | critical | climate.scope_3.not_measured | `(?i)scope\s*3[\s\S]{0,80}?(?:not\s+measured|not\s+(?:disclosed|reported|calcu...` |
| `scope_3_categories_partial` | high | climate.scope_3.partial | `(?i)(?:only\s+(?:categor(?:y|ies))|measured\s+only\s+categor(?:y|ies))\s+\d+(...` |
| `no_transition_plan` | critical | climate.no_transition_plan | `(?i)(no|absent|none)\s+(?:climate\s+)?(?:transition|net[- ]?zero|decarbon)\s+...` |
| `no_sbti_commitment` | high | climate.no_sbti | `(?i)(no|not|absent)\s+sbti(?:\s+(?:committed|validated|target))?|sbti\s*[:=]\...` |
| `no_board_oversight` | high | climate.governance.no_board | `(?i)board\s+(?:does not|has no|provides no|no formal)\s+(?:climate|oversight|...` |
| `no_scenario_analysis` | high | climate.no_scenario_analysis | `(?i)(no|not (?:performed|conducted)|absent|n[\.\/]?a)\s+scenario\s+analys(?:i...` |
| `no_third_party_assurance` | medium | climate.no_assurance | `(?i)(no|not|unassured|unverified)\s+(?:third[- ]?party|independent|external)\...` |
| `scope_2_market_only` | medium | climate.scope_2.market_only | `(?i)scope\s*2\s+(?:market[- ]?based)\s+only(?!.{0,80}location[- ]?based)|loca...` |
| `transition_risk_not_assessed` | high | climate.transition_risk.unassessed | `(?i)transition\s+risk\s+(?:not\s+(?:assessed|considered|identified|material)|...` |
| `physical_risk_not_assessed` | high | climate.physical_risk.unassessed | `(?i)physical\s+(?:climate\s+)?risk\s+(?:not\s+(?:assessed|considered|identifi...` |
| `no_targets_set` | high | climate.no_targets | `(?i)(no|absent|not\s+set)\s+(?:climate|ghg|emissions?)\s+targets?|targets?\s*...` |
| `offsetting_without_disclosure` | medium | climate.offset_only_pathway | `(?i)(net[- ]?zero|carbon[- ]?neutral)(?!.{0,400}(offsets?|removal|sbti|residu...` |
| `missing_methodology` | medium | climate.no_methodology | `(?i)methodology\s*[:=]\s*(?:n[\.\/]?a|none|undisclosed)|emissions\s+calculati...` |

