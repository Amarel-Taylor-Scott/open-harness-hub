# ESG environmental red-flag detectors (the 'E' of ESG)

*rule-pack* · `rule-pack/grep-esg-environmental-red-flags` · v0.1.0 · beta

GREP detectors for the environmental dimension of supplier
disclosures: deforestation, water pollution, hazardous-waste
mismanagement, GHG underreporting, biodiversity harm, illegal
resource extraction, single-use plastics. Aligned to:
 - EU CSDDD Art. 5(1)(b) (environmental adverse impacts)
 - EU CSRD ESRS E1-E5 disclosure standards
 - German LkSG §2(3) (environmental risks)
 - California SB 261 (climate financial risk)
 - TCFD recommendations
 - Equator Principles 4 (project finance)

Pair with `pipeline/supplier-policy-grading` for full ESG grading
(S + E + G together).

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance, climate, sustainability |
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
| `deforestation_high_risk` | critical | environmental.deforestation | `(?i)\b(deforest|clear[- ]?cut|slash[- ]?and[- ]?burn|forest conversion|primar...` |
| `illegal_logging_terms` | critical | environmental.illegal_extraction | `(?i)(illegal|unpermitted|unlicensed)\s+(?:logg|harvest|extract|timber|wood)|F...` |
| `hazardous_waste_mismanagement` | critical | environmental.hazardous_waste | `(?i)(hazardous|toxic|radioactive|persistent organic pollutant|pop)\s+(?:waste...` |
| `water_pollution` | high | environmental.water_pollution | `(?i)(discharge|effluent|runoff)\s+(?:to|into|in)\s+(?:river|stream|sea|aquife...` |
| `water_stress_sourcing` | medium | environmental.water_stress | `(?i)water[- ]?stressed?\s+(?:basin|region|area|catchment)|aqueduct\s+(?:high|...` |
| `ghg_underreporting_signal` | high | environmental.ghg_underreporting | `(?i)scope[ -]?3.*\b(not (?:calculated|reported|measured)|excluded|out of scop...` |
| `missing_climate_transition_plan` | high | environmental.no_transition_plan | `(?i)(no|absent|not (?:applicable|available))\s+(?:transition|net[- ]?zero|dec...` |
| `biodiversity_protected_area` | critical | environmental.biodiversity | `(?i)(operations|extraction|sourcing|facility)\s+(?:in|near|adjacent to)\s+(?:...` |
| `air_emissions_excessive` | high | environmental.air_emissions | `(?i)(particulate|pm[ ]?2\.5|pm[ ]?10|nox|sox|so2|voc|vocs)\s+(?:exceed|over|a...` |
| `child_pollution_exposure` | high | environmental.community_exposure | `(?i)(school|clinic|hospital|residential|kindergarten)\s+(?:within|next to|adj...` |
| `palm_oil_unsustainable` | high | environmental.palm_oil | `(?i)palm oil.*(?:not|non)[- ]?(?:rspo|sustainable|certified)|conventional pal...` |
| `cobalt_drc_artisanal_unaudited` | critical | environmental.conflict_minerals | `(?i)cobalt.*(?:drc|democratic republic|katanga|kolwezi|likasi).*(?:artisanal|...` |
| `single_use_plastic` | low | environmental.packaging | `(?i)single[- ]?use plastic|non[- ]?recyclable.*packaging|plastic.*not collect...` |
| `ozone_depleting_substance` | high | environmental.ozone_depleting | `(?i)(cfc|hcfc|hfc|hydrochlorofluorocarbon|methyl bromide|halon)\s+(?:use|emis...` |
| `land_clearing_legacy` | high | environmental.deforestation_legacy | `(?i)(land|plot|area|hectare|forest)\s+(?:was |were |has been )?(?:cleared|def...` |
| `scope_3_excluded_categories` | medium | environmental.scope_3_underreporting | `(?i)scope[ -]?3.*(?:cat(?:egory)?\s*\d+).*(?:null|excluded|not (?:measured|re...` |
| `no_third_party_ghg_verification` | medium | environmental.ghg_no_verification | `(?i)(?:ghg|emissions|carbon)\s+(?:not|no|never)\s+(?:third[- ]?party|external...` |
| `near_protected_area` | high | environmental.biodiversity_proximity | `(?i)(?:within|near|adjacent|kilometre|km|miles?)\s+(?:of|to|from)\s+(?:(?:nat...` |
| `untreated_dye_effluent` | critical | environmental.water_pollution.textile_dye | `(?i)(?:dye|tannery|leather|textile)\s+effluent.*(?:discharge|release|dump|dra...` |

