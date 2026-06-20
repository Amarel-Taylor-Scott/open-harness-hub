# Employee Relations Investigation grep flags

*rule-pack* · `rule-pack/grep-employee-relations-investigation-flags` · v0.1.0 · experimental

Ten local triage detectors for employee relations investigation packets.

| axis | value |
|---|---|
| industry | hr.performance, hr.hiring |
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
| `retaliation_risk` | critical | employee_relations_investigation.retaliation_risk | `(?i)retaliation.{0,36}risk` |
| `witness_missing` | critical | employee_relations_investigation.witness_missing | `(?i)witness.{0,36}missing` |
| `harassment_allegation` | high | employee_relations_investigation.harassment_allegation | `(?i)harassment.{0,36}allegation` |
| `conflict_of_interest` | high | employee_relations_investigation.conflict_of_interest | `(?i)conflict.{0,36}of.{0,36}interest` |
| `confidentiality_breach` | high | employee_relations_investigation.confidentiality_breach | `(?i)confidentiality.{0,36}breach` |
| `discipline_inconsistent` | high | employee_relations_investigation.discipline_inconsistent | `(?i)discipline.{0,36}inconsistent` |
| `timeline_gap` | medium | employee_relations_investigation.timeline_gap | `(?i)timeline.{0,36}gap` |
| `policy_violation` | medium | employee_relations_investigation.policy_violation | `(?i)policy.{0,36}violation` |
| `manager_accused` | medium | employee_relations_investigation.manager_accused | `(?i)manager.{0,36}accused` |
| `protected_activity` | medium | employee_relations_investigation.protected_activity | `(?i)protected.{0,36}activity` |
| `scale_expansion_v1_critical_signal_01` | high | grep-employee-relations-investigation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}employee.{0,24}relations.{0,24}invest...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-employee-relations-investigation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investigatio...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-employee-relations-investigation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-employee-relations-investigation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investi...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-employee-relations-investigation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-employee-relations-investigation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investiga...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-employee-relations-investigation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}employee.{0,24}relations.{0,24}inve...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-employee-relations-investigation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}employee.{0,24}relations.{0,24}inves...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-employee-relations-investigation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}employee.{0,24}relations.{0,24}invest...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-employee-relations-investigation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investigatio...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-employee-relations-investigation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-employee-relations-investigation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investi...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-employee-relations-investigation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-employee-relations-investigation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investiga...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-employee-relations-investigation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}employee.{0,24}relations.{0,24}inve...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-employee-relations-investigation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}employee.{0,24}relations.{0,24}inves...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-employee-relations-investigation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}employee.{0,24}relations.{0,24}invest...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-employee-relations-investigation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investigatio...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-employee-relations-investigation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-employee-relations-investigation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investi...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-employee-relations-investigation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-employee-relations-investigation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investiga...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-employee-relations-investigation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}employee.{0,24}relations.{0,24}inve...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-employee-relations-investigation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}employee.{0,24}relations.{0,24}inves...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-employee-relations-investigation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}employee.{0,24}relations.{0,24}invest...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-employee-relations-investigation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investigatio...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-employee-relations-investigation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-employee-relations-investigation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investi...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-employee-relations-investigation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-employee-relations-investigation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investiga...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-employee-relations-investigation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}employee.{0,24}relations.{0,24}inve...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-employee-relations-investigation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}employee.{0,24}relations.{0,24}inves...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-employee-relations-investigation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}employee.{0,24}relations.{0,24}invest...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-employee-relations-investigation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investigatio...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-employee-relations-investigation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-employee-relations-investigation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}employee.{0,24}relations.{0,24}investi...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-employee-relations-investigation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investig...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-employee-relations-investigation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}employee.{0,24}relations.{0,24}investiga...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-employee-relations-investigation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}employee.{0,24}relations.{0,24}inve...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-employee-relations-investigation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}employee.{0,24}relations.{0,24}inves...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-employee-relations-investigation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-employee-relations-investigation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-employee-relations-investigation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

