# Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags

*rule-pack* · `rule-pack/grep-biosecurity-flags` · v0.1.0 · beta

Detectors for 42 CFR 73 / BMBL / WHO LBM4 / DURC compliance gaps.

| axis | value |
|---|---|
| industry | biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc |
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
| `unescorted_access_no_sra` | critical | biosec.access.no_sra | `(?i)(?:without\s+(?:an\s+)?active\s+(?:fbi\s+)?(?:security\s+risk\s+assessmen...` |
| `inventory_variance_form4` | critical | biosec.inventory.variance | `(?i)(?:(?<!no\s)(?<!zero\s)(?:select\s+agent\s+)?inventory\s+(?:mismatch|vari...` |
| `dual_key_breached` | critical | biosec.access.dual_key_breached | `(?i)(?:dual[- ]?key|two[- ]?person)\s+(?:procedure|access|requirement)\s+(?:w...` |
| `gain_of_function_no_durc_p3co` | critical | biosec.durc.no_review | `(?i)(?:gain[- ]?of[- ]?function|aerosol(?:ization)?\s+(?:protocol|experiment)...` |
| `release_loss_unreported_7d` | critical | biosec.release.unreported | `(?i)(?:spill|release|loss|theft)[\s\S]{0,200}?(?:not\s+reported\s+to\s+(?:cdc...` |
| `transfer_form2_missing` | high | biosec.transfer.no_form2 | `(?i)(?:shipped|transferred)[\s\S]{0,200}?(?:without\s+(?:the\s+)?(?:aphis\s*[...` |
| `bsc_certification_overdue` | high | biosec.bsc.cert_overdue | `(?i)(?:bsc[- ]?ii|biosafety\s+cabinet)\s+(?:annual\s+)?(?:recertification|cer...` |
| `hepa_leak_test_overdue` | medium | biosec.hepa.overdue | `(?i)hepa\s+(?:push[- ]?through\s+)?(?:filter\s+)?(?:leak|integrity|pao|dop)\s...` |
| `autoclave_unvalidated_cycle` | high | biosec.decon.unvalidated | `(?i)(?:autoclave|sterilization)\s+(?:short\s+cycle|unvalidated\s+cycle|cycle\...` |
| `ppe_doffing_violation` | medium | biosec.ppe.doffing | `(?i)ppe\s+doffing\s+(?:sequence\s+)?violation|doffing\s+(?:sequence\s+)?(?:vi...` |
| `visitor_log_incomplete` | low | biosec.visitor.log_incomplete | `(?i)visitor\s+log\s+(?:incomplete|gap|missing|not\s+maintained)` |
| `scale_expansion_v1_critical_signal_01` | high | grep-biosecurity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-biosecurity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evidence...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-biosecurity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-biosecurity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-biosecurity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-biosecurity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-biosecurity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-biosecurity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-biosecurity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-biosecurity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evidence...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-biosecurity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-biosecurity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-biosecurity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-biosecurity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-biosecurity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-biosecurity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-biosecurity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-biosecurity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evidence...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-biosecurity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-biosecurity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-biosecurity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-biosecurity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-biosecurity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-biosecurity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-biosecurity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-biosecurity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evidence...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-biosecurity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-biosecurity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-biosecurity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-biosecurity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-biosecurity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-biosecurity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-biosecurity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-biosecurity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evidence...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-biosecurity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-biosecurity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-biosecurity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-biosecurity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:evide...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-biosecurity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-biosecurity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}biosecurity.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-biosecurity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-biosecurity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-biosecurity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-biosecurity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-biosecurity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-biosecurity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-biosecurity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-biosecurity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-biosecurity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-biosecurity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

