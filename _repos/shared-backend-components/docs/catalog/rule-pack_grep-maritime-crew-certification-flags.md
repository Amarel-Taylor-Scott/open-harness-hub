# Maritime Crew Certification grep flags

*rule-pack* · `rule-pack/grep-maritime-crew-certification-flags` · v0.1.0 · experimental

Ten local triage detectors for maritime crew certification packets.

| axis | value |
|---|---|
| industry | maritime.safety, transportation.maritime |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `STCW_certificate` | critical | maritime_crew_certification.STCW_certificate | `(?i)STCW.{0,36}certificate` |
| `medical_expired` | critical | maritime_crew_certification.medical_expired | `(?i)medical.{0,36}expired` |
| `rest_hours` | high | maritime_crew_certification.rest_hours | `(?i)rest.{0,36}hours` |
| `watchkeeping` | high | maritime_crew_certification.watchkeeping | `(?i)watchkeeping` |
| `flag_state` | high | maritime_crew_certification.flag_state | `(?i)flag.{0,36}state` |
| `crew_matrix` | high | maritime_crew_certification.crew_matrix | `(?i)crew.{0,36}matrix` |
| `endorsement_missing` | medium | maritime_crew_certification.endorsement_missing | `(?i)endorsement.{0,36}missing` |
| `training_gap` | medium | maritime_crew_certification.training_gap | `(?i)training.{0,36}gap` |
| `safe_manning` | medium | maritime_crew_certification.safe_manning | `(?i)safe.{0,36}manning` |
| `fatigue_risk` | medium | maritime_crew_certification.fatigue_risk | `(?i)fatigue.{0,36}risk` |
| `scale_expansion_v1_critical_signal_01` | high | grep-maritime-crew-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}maritime.{0,24}crew.{0,24}certificati...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-maritime-crew-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification.{0,...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-maritime-crew-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-maritime-crew-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certificatio...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-maritime-crew-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-maritime-crew-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification....` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-maritime-crew-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}maritime.{0,24}crew.{0,24}certifica...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-maritime-crew-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}maritime.{0,24}crew.{0,24}certificat...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-maritime-crew-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}maritime.{0,24}crew.{0,24}certificati...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-maritime-crew-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification.{0,...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-maritime-crew-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-maritime-crew-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certificatio...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-maritime-crew-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-maritime-crew-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification....` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-maritime-crew-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}maritime.{0,24}crew.{0,24}certifica...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-maritime-crew-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}maritime.{0,24}crew.{0,24}certificat...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-maritime-crew-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}maritime.{0,24}crew.{0,24}certificati...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-maritime-crew-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification.{0,...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-maritime-crew-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-maritime-crew-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certificatio...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-maritime-crew-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-maritime-crew-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification....` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-maritime-crew-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}maritime.{0,24}crew.{0,24}certifica...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-maritime-crew-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}maritime.{0,24}crew.{0,24}certificat...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-maritime-crew-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}maritime.{0,24}crew.{0,24}certificati...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-maritime-crew-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification.{0,...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-maritime-crew-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-maritime-crew-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certificatio...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-maritime-crew-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-maritime-crew-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification....` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-maritime-crew-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}maritime.{0,24}crew.{0,24}certifica...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-maritime-crew-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}maritime.{0,24}crew.{0,24}certificat...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-maritime-crew-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}maritime.{0,24}crew.{0,24}certificati...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-maritime-crew-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification.{0,...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-maritime-crew-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-maritime-crew-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}maritime.{0,24}crew.{0,24}certificatio...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-maritime-crew-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-maritime-crew-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}maritime.{0,24}crew.{0,24}certification....` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-maritime-crew-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}maritime.{0,24}crew.{0,24}certifica...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-maritime-crew-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}maritime.{0,24}crew.{0,24}certificat...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-maritime-crew-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-maritime-crew-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-maritime-crew-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

