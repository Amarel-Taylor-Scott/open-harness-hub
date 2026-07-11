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
| `scale_expansion_v1_critical_signal_01` | high | grep-esg-environmental-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-esg-environmental-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-esg-environmental-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-esg-environmental-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,2...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-esg-environmental-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-esg-environmental-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-esg-environmental-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}environmental.{0,24}red.{...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-esg-environmental-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-esg-environmental-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-esg-environmental-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-esg-environmental-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-esg-environmental-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,2...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-esg-environmental-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-esg-environmental-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-esg-environmental-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}environmental.{0,24}red.{...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-esg-environmental-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-esg-environmental-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-esg-environmental-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-esg-environmental-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-esg-environmental-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,2...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-esg-environmental-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-esg-environmental-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-esg-environmental-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}environmental.{0,24}red.{...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-esg-environmental-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-esg-environmental-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-esg-environmental-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-esg-environmental-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-esg-environmental-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,2...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-esg-environmental-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-esg-environmental-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-esg-environmental-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}environmental.{0,24}red.{...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-esg-environmental-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-esg-environmental-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-esg-environmental-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-esg-environmental-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-esg-environmental-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,2...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-esg-environmental-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-esg-environmental-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-esg-environmental-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}environmental.{0,24}red.{...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-esg-environmental-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}environmental.{0,24}red.{0...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-esg-environmental-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-esg-environmental-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-esg-environmental-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-esg-environmental-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-esg-environmental-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-esg-environmental-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-esg-environmental-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

