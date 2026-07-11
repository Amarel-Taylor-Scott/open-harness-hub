# Workforce Training Certification grep flags

*rule-pack* · `rule-pack/grep-workforce-training-certification-flags` · v0.1.0 · experimental

Ten local triage detectors for workforce training certification packets.

| axis | value |
|---|---|
| industry | education.workforce, hr.performance |
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
| `certification_expired` | critical | workforce_training_certification.certification_expired | `(?i)certification.{0,36}expired` |
| `prerequisite_missing` | critical | workforce_training_certification.prerequisite_missing | `(?i)prerequisite.{0,36}missing` |
| `assessment_failed` | high | workforce_training_certification.assessment_failed | `(?i)assessment.{0,36}failed` |
| `proctor_issue` | high | workforce_training_certification.proctor_issue | `(?i)proctor.{0,36}issue` |
| `accommodation_request` | high | workforce_training_certification.accommodation_request | `(?i)accommodation.{0,36}request` |
| `training_overdue` | high | workforce_training_certification.training_overdue | `(?i)training.{0,36}overdue` |
| `roster_mismatch` | medium | workforce_training_certification.roster_mismatch | `(?i)roster.{0,36}mismatch` |
| `competency_gap` | medium | workforce_training_certification.competency_gap | `(?i)competency.{0,36}gap` |
| `badge_revoked` | medium | workforce_training_certification.badge_revoked | `(?i)badge.{0,36}revoked` |
| `audit_sample` | medium | workforce_training_certification.audit_sample | `(?i)audit.{0,36}sample` |
| `scale_expansion_v1_critical_signal_01` | high | grep-workforce-training-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}workforce.{0,24}training.{0,24}certif...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-workforce-training-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certificatio...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-workforce-training-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-workforce-training-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certifi...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-workforce-training-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-workforce-training-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certifica...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-workforce-training-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}workforce.{0,24}training.{0,24}cert...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-workforce-training-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}workforce.{0,24}training.{0,24}certi...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-workforce-training-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}workforce.{0,24}training.{0,24}certif...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-workforce-training-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certificatio...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-workforce-training-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-workforce-training-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certifi...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-workforce-training-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-workforce-training-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certifica...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-workforce-training-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}workforce.{0,24}training.{0,24}cert...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-workforce-training-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}workforce.{0,24}training.{0,24}certi...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-workforce-training-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}workforce.{0,24}training.{0,24}certif...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-workforce-training-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certificatio...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-workforce-training-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-workforce-training-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certifi...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-workforce-training-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-workforce-training-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certifica...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-workforce-training-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}workforce.{0,24}training.{0,24}cert...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-workforce-training-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}workforce.{0,24}training.{0,24}certi...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-workforce-training-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}workforce.{0,24}training.{0,24}certif...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-workforce-training-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certificatio...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-workforce-training-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-workforce-training-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certifi...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-workforce-training-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-workforce-training-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certifica...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-workforce-training-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}workforce.{0,24}training.{0,24}cert...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-workforce-training-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}workforce.{0,24}training.{0,24}certi...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-workforce-training-certification-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}workforce.{0,24}training.{0,24}certif...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-workforce-training-certification-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certificatio...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-workforce-training-certification-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-workforce-training-certification-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}workforce.{0,24}training.{0,24}certifi...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-workforce-training-certification-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certific...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-workforce-training-certification-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}workforce.{0,24}training.{0,24}certifica...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-workforce-training-certification-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}workforce.{0,24}training.{0,24}cert...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-workforce-training-certification-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}workforce.{0,24}training.{0,24}certi...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-workforce-training-certification-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-workforce-training-certification-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-workforce-training-certification-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-workforce-training-certification-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-workforce-training-certification-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-workforce-training-certification-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-workforce-training-certification-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

