# NERC CIP compliance red-flag detectors

*rule-pack* · `rule-pack/grep-nerc-cip-flags` · v0.1.0 · beta

Detectors for NERC CIP gaps.

| axis | value |
|---|---|
| industry | energy, energy.grid, security, compliance |
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
| `no_baseline_config` | critical | energy.cip.no_baseline | `(?i)(?:no|absent|missing)\s+baseline\s+configuration|baseline\s+configuration...` |
| `unauthorized_firmware` | critical | energy.cip.unauthorized_firmware | `(?i)unauthorized\s+(?:firmware|software|patch)|firmware\s+(?:installed|deploy...` |
| `expired_authorization` | high | energy.cip.expired_authorization | `(?i)(?:user\s+)?authorization\s+(?:expired|lapsed|past\s+due)|access\s+(?:not...` |
| `esp_gap` | critical | energy.cip.esp_gap | `(?i)(?:electronic\s+security\s+perimeter|\besp\b)\s+(?:gap|inactive|disabled|...` |
| `psp_gap` | critical | energy.cip.psp_gap | `(?i)(?:physical\s+security\s+perimeter|\bpsp\b)\s+(?:breach|unauthorized\s+ac...` |
| `unpatched_vuln_35d` | high | energy.cip.unpatched_35d | `(?i)(?:unpatched|outstanding)\s+(?:vulnerability|cve)\s+(?:over|exceed(?:ing|...` |
| `no_irp` | high | energy.cip.no_incident_plan | `(?i)(?:no|absent|missing)\s+(?:cyber\s+)?incident\s+response\s+plan|cip[- ]?0...` |
| `no_recovery_plan` | high | energy.cip.no_recovery_plan | `(?i)(?:no|absent|missing|untested)\s+recovery\s+plan|cip[- ]?009\s+plan\s+(?:...` |
| `supply_chain_risk_unassessed` | medium | energy.cip.supply_chain | `(?i)(?:vendor|supplier|supply[- ]?chain)\s+(?:risk|cyber)\s+(?:not\s+(?:asses...` |
| `bes_cyber_uncategorized` | critical | energy.cip.no_categorization | `(?i)bes\s+cyber\s+(?:asset|system)\s+(?:not\s+categorized|impact\s+rating\s+(...` |
| `personnel_risk_assessment_lapsed` | high | energy.cip.pra_lapsed | `(?i)(?:personnel\s+)?risk\s+assessment\s+(?:lapsed|overdue|past\s+due)|crimin...` |
| `removable_media_uncontrolled` | high | energy.cip.removable_media | `(?i)(?<!no\s)\b(?:removable\s+media|usb\s+drives?|portable\s+drives?)\s+(?:un...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-nerc-cip-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-nerc-cip-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-nerc-cip-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-nerc-cip-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-nerc-cip-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-nerc-cip-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-nerc-cip-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-nerc-cip-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-nerc-cip-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-nerc-cip-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-nerc-cip-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-nerc-cip-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-nerc-cip-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-nerc-cip-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-nerc-cip-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-nerc-cip-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-nerc-cip-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-nerc-cip-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-nerc-cip-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-nerc-cip-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-nerc-cip-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-nerc-cip-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-nerc-cip-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-nerc-cip-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-nerc-cip-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-nerc-cip-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-nerc-cip-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-nerc-cip-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-nerc-cip-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-nerc-cip-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-nerc-cip-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-nerc-cip-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-nerc-cip-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-nerc-cip-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-nerc-cip-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-nerc-cip-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-nerc-cip-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-nerc-cip-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-nerc-cip-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-nerc-cip-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}nerc.{0,24}cip.{0,24}flags).{0,160}(...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-nerc-cip-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-nerc-cip-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-nerc-cip-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-nerc-cip-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-nerc-cip-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-nerc-cip-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-nerc-cip-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-nerc-cip-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-nerc-cip-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-nerc-cip-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

