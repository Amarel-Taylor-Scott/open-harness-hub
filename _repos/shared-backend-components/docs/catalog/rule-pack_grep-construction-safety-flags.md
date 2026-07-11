# Construction safety red-flag detectors (OSHA 1926)

*rule-pack* · `rule-pack/grep-construction-safety-flags` · v0.1.0 · beta

Detectors for OSHA Focus Four + scaffolding + excavation + PPE.

| axis | value |
|---|---|
| industry | construction, construction.safety |
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
| `no_fall_protection_above_6ft` | critical | construction.fall_protection.missing | `(?i)(?:work|working)\s+(?:at|above)\s+(?:height|elevat\w+)(?:\s+(?:of\s+)?(?:...` |
| `unsafe_scaffold` | high | construction.scaffold.deficiency | `(?i)scaffold(?:ing)?\s+(?:missing\s+(?:guardrail|toeboard|midrail)|not\s+insp...` |
| `excavation_no_protective_system` | critical | construction.excavation.no_protective_system | `(?i)excavation\s+(?:over|deeper\s+than|>\s*)\s*5\s*(?:ft|feet|')(?!.{0,200}(?...` |
| `no_competent_person` | high | construction.competent_person.missing | `(?i)(?:no|absent|undesignated)\s+competent\s+person(?:\s+for\s+(?:excavation|...` |
| `energized_work_no_eep` | critical | construction.electrical.energized_no_plan | `(?i)energized\s+(?:electrical\s+)?work(?!.{0,200}(?:electrical\s+energy\s+pla...` |
| `missing_loto` | critical | construction.electrical.no_loto | `(?i)(?:no|absent|missing|skipped)\s+(?:lockout[- ]?tagout|loto)\s+(?:procedur...` |
| `ppe_not_required` | high | construction.ppe.not_required | `(?i)(?:hard[- ]?hat|safety[- ]?glasses|hi[- ]?vis|fall[- ]?harness|gloves)\s+...` |
| `crane_no_signal_person` | high | construction.crane.no_signal_person | `(?i)crane\s+(?:lift|operation)(?!.{0,200}(?:signal\s+person|qualified\s+signa...` |
| `near_miss_not_reported` | medium | construction.reporting.near_miss | `(?i)near[- ]?miss(?:es)?\s+(?:not\s+reported|not\s+logged|verbal\s+only)` |
| `toolbox_talk_skipped` | low | construction.training.toolbox_skipped | `(?i)(?:toolbox\s+talk|pre[- ]?task\s+plan|jha)\s+(?:skipped|missed|not\s+(?:c...` |
| `silica_no_exposure_plan` | high | construction.silica.no_control | `(?i)silica\s+(?:exposure|cutting|grinding|drilling)(?!.{0,200}(?:exposure\s+c...` |
| `confined_space_no_permit` | critical | construction.confined_space.no_permit | `(?i)confined\s+space(?!.{0,200}(?:permit|attendant|rescue|atmospheric\s+(?:te...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-construction-safety-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}construction.{0,24}safety.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-construction-safety-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-construction-safety-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-construction-safety-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-construction-safety-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_06` | high | grep-construction-safety-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-construction-safety-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}construction.{0,24}safety.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-construction-safety-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}construction.{0,24}safety.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-construction-safety-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}construction.{0,24}safety.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-construction-safety-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-construction-safety-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-construction-safety-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-construction-safety-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-construction-safety-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-construction-safety-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}construction.{0,24}safety.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-construction-safety-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}construction.{0,24}safety.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-construction-safety-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}construction.{0,24}safety.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-construction-safety-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-construction-safety-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-construction-safety-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-construction-safety-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-construction-safety-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-construction-safety-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}construction.{0,24}safety.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-construction-safety-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}construction.{0,24}safety.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-construction-safety-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}construction.{0,24}safety.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-construction-safety-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-construction-safety-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-construction-safety-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-construction-safety-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_30` | high | grep-construction-safety-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-construction-safety-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}construction.{0,24}safety.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-construction-safety-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}construction.{0,24}safety.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-construction-safety-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}construction.{0,24}safety.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-construction-safety-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-construction-safety-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-construction-safety-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}construction.{0,24}safety.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-construction-safety-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-construction-safety-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}construction.{0,24}safety.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-construction-safety-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}construction.{0,24}safety.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-construction-safety-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}construction.{0,24}safety.{0,24}flag...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-construction-safety-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-construction-safety-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-construction-safety-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-construction-safety-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-construction-safety-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-construction-safety-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-construction-safety-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-construction-safety-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-construction-safety-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-construction-safety-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

