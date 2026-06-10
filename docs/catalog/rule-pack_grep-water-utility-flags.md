# Water utility SDWA / LCRR / AWIA red-flag detectors

*rule-pack* · `rule-pack/grep-water-utility-flags` · v0.1.0 · beta

GREP detectors for SDWA compliance gaps + acute risks.

| axis | value |
|---|---|
| industry | water_utility, water_utility.lcr, water_utility.sdwa |
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
| `e_coli_mcl_violation` | critical | water.acute.e_coli | `(?i)(?:e[\.\s]\s*coli|escherichia\s+coli|fecal\s+coliform)\s+(?:positive|dete...` |
| `nitrate_above_mcl` | critical | water.acute.nitrate | `(?i)nitrate.{0,40}(?:\d{1,2}(?:\.\d+)?)\s*mg(?:/|\s*per\s*)?l(?!.{0,200}below...` |
| `lead_above_al` | critical | water.lead.action_level_exceeded | `(?i)lead\s+(?:90th[- ]?percentile|al|action\s+level)\s+(?:exceed|over|above|>...` |
| `lcrr_inventory_missing` | critical | water.lcrr.no_inventory | `(?i)(?:lead\s+service\s+line\s+inventory|lsli|lsl\s+inventory)\s+(?:not\s+(?:...` |
| `pn_tier_1_missed` | critical | water.public_notification.tier_1_missed | `(?i)tier\s+1\s+(?:public\s+)?notification\s+(?:missed|past\s+24\s+hours|not\s...` |
| `awia_rra_overdue` | high | water.awia.rra_overdue | `(?i)(?:awia\s+)?(?:risk\s+and\s+resilience\s+assessment|rra)\s+(?:overdue|exp...` |
| `scada_default_credentials` | critical | water.scada.default_credentials | `(?i)scada\s+(?:system|hmi|plc)\s+(?:default\s+(?:password|credentials)|unchan...` |
| `ccr_missing` | high | water.ccr.missing | `(?i)(?:consumer\s+confidence\s+report|ccr)\s+(?:not\s+(?:issued|published)|mi...` |
| `trihalomethane_mcl` | high | water.dbpr.tthm_mcl | `(?i)(?:tthm|trihalomethanes?|total\s+thm)\s+(?:above|exceed|violation)\s+\d{1...` |
| `haa5_mcl` | high | water.dbpr.haa5_mcl | `(?i)(?:haa5|haloacetic\s+acids?)\s+(?:above|exceed|violation)\s+\d{1,3}\s*(?:...` |
| `tt_violation_filtration` | high | water.tt.filtration | `(?i)(?:filtration|treatment\s+technique|tt)\s+(?:violation|failure)|turbidity...` |
| `monitoring_skipped` | medium | water.monitoring.skipped | `(?i)(?:monitoring|sampling)\s+(?:not\s+(?:performed|conducted)|skipped|missed...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-water-utility-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-water-utility-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-water-utility-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-water-utility-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-water-utility-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-water-utility-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-water-utility-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}water.{0,24}utility.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-water-utility-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-water-utility-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-water-utility-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-water-utility-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-water-utility-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-water-utility-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-water-utility-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-water-utility-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}water.{0,24}utility.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-water-utility-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-water-utility-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-water-utility-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-water-utility-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-water-utility-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-water-utility-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-water-utility-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-water-utility-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}water.{0,24}utility.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-water-utility-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-water-utility-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-water-utility-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-water-utility-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-water-utility-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-water-utility-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-water-utility-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-water-utility-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}water.{0,24}utility.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-water-utility-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-water-utility-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-water-utility-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-water-utility-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-water-utility-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-water-utility-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-water-utility-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-water-utility-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}water.{0,24}utility.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-water-utility-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}water.{0,24}utility.{0,24}flags).{0,...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-water-utility-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-water-utility-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-water-utility-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-water-utility-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-water-utility-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-water-utility-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-water-utility-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-water-utility-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-water-utility-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-water-utility-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

