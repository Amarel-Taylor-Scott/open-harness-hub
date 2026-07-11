# UN SDG goal-mapping classifier rules (17 goals / 169 targets)

*rule-pack* · `rule-pack/classifier-sdg-mapping` · v0.1.0 · experimental

Classifier-style rules that map free-text claim fragments to the
most likely SDG goals + targets they touch. Each rule defines
labeled examples + a confidence threshold for a lightweight
classifier (zero-shot, BM25 + cosine, or fine-tuned).

Use as a FIRST-PASS clustering step in `pipeline/sdg-alignment-
assessment` to narrow the candidate goal set before deeper
target-level analysis.

Coverage: all 17 goals; top 5 most-likely targets per goal.

| axis | value |
|---|---|
| industry | esg, sustainability, nonprofit, government, cross_industry |
| capability | classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `classifier`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `sdg_1_poverty` | - | - | `` |
| `sdg_2_zero_hunger` | - | - | `` |
| `sdg_3_health_wellbeing` | - | - | `` |
| `sdg_4_quality_education` | - | - | `` |
| `sdg_5_gender_equality` | - | - | `` |
| `sdg_6_water_sanitation` | - | - | `` |
| `sdg_7_clean_energy` | - | - | `` |
| `sdg_8_decent_work` | - | - | `` |
| `sdg_9_industry_innovation` | - | - | `` |
| `sdg_10_reduced_inequality` | - | - | `` |
| `sdg_11_sustainable_cities` | - | - | `` |
| `sdg_12_responsible_consumption` | - | - | `` |
| `sdg_13_climate_action` | - | - | `` |
| `sdg_14_life_below_water` | - | - | `` |
| `sdg_15_life_on_land` | - | - | `` |
| `sdg_16_peace_justice` | - | - | `` |
| `sdg_17_partnerships` | - | - | `` |

