# Agriculture compliance flags (USDA / GAP / NOP organic)

*rule-pack* · `rule-pack/grep-agriculture-compliance-flags` · v0.1.0 · beta

Detectors for ag-supply-chain compliance gaps.

| axis | value |
|---|---|
| industry | agriculture_compliance, agriculture_compliance.usda, agriculture_compliance.organic, agriculture_compliance.gap |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `pesticide_rei_violation` | critical | agriculture.wps.rei_violation | `(?i)(?:rei|restricted[- ]?entry[- ]?interval)\s+(?:violation|breach|exceeded)...` |
| `pesticide_phi_violation` | critical | agriculture.pesticide.phi_violation | `(?i)(?:phi|pre[- ]?harvest[- ]?interval)\s+(?:violation|breach|short|exceeded...` |
| `mrl_exceedance` | critical | agriculture.pesticide.mrl | `(?i)(?:mrl|maximum\s+residue\s+limit)\s+(?:exceed|over|violation|above)|resid...` |
| `organic_split_op_unsegregated` | critical | agriculture.organic.split_op | `(?i)(?:split[- ]?operation|parallel\s+production)\s+(?:same\s+crop|unsegregat...` |
| `prohibited_substance_organic` | critical | agriculture.organic.prohibited | `(?i)(?:synthetic\s+pesticide|prohibited\s+(?:substance|input))\s+(?:on|used\s...` |
| `water_quality_e_coli_exceed` | critical | agriculture.water.e_coli | `(?i)(?:e[\.\s]\s*coli|geometric\s+mean)\s+(?:exceed|>|above)\s+(?:126|410)\s+...` |
| `untrained_worker` | high | agriculture.training.untrained | `(?i)worker\s+(?:trained|certification)\s+(?:not\s+(?:completed|documented)|ex...` |
| `no_traceability_lot` | high | agriculture.traceability.no_lot | `(?i)(?:lot|traceability|batch)\s+(?:tracking|number)\s+(?:missing|incomplete|...` |
| `no_recall_plan` | medium | agriculture.recall.no_plan | `(?i)(?:recall|withdrawal)\s+(?:plan|procedure)\s+(?:not\s+(?:documented|teste...` |
| `label_misbranding` | medium | agriculture.labeling.misbranding | `(?i)label(?:ing)?\s+(?:misbrand|noncompliant|misleading)|country[- ]?of[- ]?o...` |
| `child_labor_indicator` | critical | agriculture.labor.child | `(?i)(?:child|minor|under[- ]?age)\s+(?:labor|worker|harvester)|harkin[- ]?engel` |

