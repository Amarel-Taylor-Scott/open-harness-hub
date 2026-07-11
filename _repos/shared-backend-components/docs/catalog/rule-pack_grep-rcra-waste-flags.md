# RCRA hazardous waste + e-Manifest + DOT HMR flags

*rule-pack* · `rule-pack/grep-rcra-waste-flags` · v0.1.0 · beta

Detectors for 40 CFR 260-279 + e-Manifest + DOT 49 CFR 172 compliance gaps.

| axis | value |
|---|---|
| industry | waste, waste.rcra_tsdf, waste.generator, waste.universal |
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
| `generator_status_miscategorized_lqg` | critical | waste.generator.miscategorized | `(?i)(?:self[- ]?identified|categorized)\s+as\s+(?:a\s+)?(?:small\s+quantity\s...` |
| `accumulation_past_limit` | critical | waste.accumulation.exceeded | `(?i)(?:drums?|containers?)[\s\S]{0,200}?(?:over\s+1[0-9]{2}\s+days?\s+old|pas...` |
| `container_marking_missing` | high | waste.container.marking_missing | `(?i)(?:no\s+accumulation\s+start\s+date|drums?\s+(?:with|observed)\s+(?:with\...` |
| `secondary_containment_missing` | critical | waste.tank.no_secondary | `(?i)(?:tank[\s\S]{0,80}?(?:sat|located|positioned)[\s\S]{0,80}?(?:bare\s+asph...` |
| `incompatible_wastes_co_stored` | critical | waste.storage.incompatible | `(?i)(?:acid[\s\S]{0,80}?(?:cyanide|plating\s+sludge)|cyanide[\s\S]{0,80}?acid...` |
| `weekly_inspection_gap` | medium | waste.inspection.gap | `(?i)(?:weekly\s+(?:container\s+|tank\s+)?inspection|inspection\s+log)[\s\S]{0...` |
| `ldr_notification_missing` | critical | waste.ldr.missing | `(?i)(?:ldr|land\s+disposal\s+restriction)\s+notification\s+(?:missing|absent|...` |
| `dot_hazmat_training_missing` | high | waste.dot.no_training | `(?i)(?:signing\s+employee|shipping\s+signatory)\s+(?:held\s+)?(?:no\s+(?:curr...` |
| `contingency_plan_not_shared_lepc` | medium | waste.contingency.no_lepc | `(?i)(?:contingency\s+plan|emergency\s+plan)[\s\S]{0,200}?(?:never\s+(?:been\s...` |
| `satellite_accumulation_exceed_55gal` | medium | waste.satellite.exceeded | `(?i)satellite\s+accumulation[\s\S]{0,200}?(?:over\s+55\s+gal|exceed(?:ing|s|e...` |
| `biennial_report_missing` | medium | waste.biennial.missing | `(?i)(?:biennial\s+report|form\s+8700[- ]?13)\s+(?:missing|not\s+(?:filed|subm...` |
| `permit_expired_or_interim_no_part_b` | critical | waste.permit.expired | `(?i)(?:part\s+b\s+permit|tsdf\s+permit)\s+(?:expired|in\s+interim\s+status\s+...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-rcra-waste-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-rcra-waste-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-rcra-waste-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-rcra-waste-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-rcra-waste-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-rcra-waste-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-rcra-waste-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,16...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-rcra-waste-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-rcra-waste-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-rcra-waste-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-rcra-waste-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-rcra-waste-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-rcra-waste-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-rcra-waste-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-rcra-waste-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,16...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-rcra-waste-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-rcra-waste-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-rcra-waste-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-rcra-waste-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-rcra-waste-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-rcra-waste-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-rcra-waste-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-rcra-waste-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,16...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-rcra-waste-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-rcra-waste-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-rcra-waste-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-rcra-waste-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-rcra-waste-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-rcra-waste-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-rcra-waste-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-rcra-waste-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,16...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-rcra-waste-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-rcra-waste-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-rcra-waste-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-rcra-waste-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-rcra-waste-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-rcra-waste-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-rcra-waste-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-rcra-waste-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,16...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-rcra-waste-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}rcra.{0,24}waste.{0,24}flags).{0,160...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-rcra-waste-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-rcra-waste-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-rcra-waste-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-rcra-waste-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-rcra-waste-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-rcra-waste-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-rcra-waste-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-rcra-waste-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-rcra-waste-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-rcra-waste-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

