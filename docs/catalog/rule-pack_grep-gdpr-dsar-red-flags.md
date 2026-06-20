# GDPR DSAR red-flag detectors

*rule-pack* · `rule-pack/grep-gdpr-dsar-red-flags` · v0.1.0 · beta

GREP detectors for GDPR Data Subject Access Request handling
red flags: missing identity verification, missing-lawful-basis,
unlawful erasure refusal, missing transfer safeguards, missing
breach-notification trace, dark-pattern consent.

| axis | value |
|---|---|
| industry | privacy, privacy.gdpr, privacy.dsar, compliance |
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
| `missing_identity_verification` | critical | gdpr.dsar.no_id_verification | `(?i)(?:no|absent|skipped|not performed)\s+identity\s+verification|identity\s+...` |
| `missing_lawful_basis` | critical | gdpr.lawful_basis.missing | `(?i)(?:no|absent)\s+lawful\s+basis(?:\s+identified)?|lawful\s+basis\s*[:=]\s*...` |
| `deadline_missed` | high | gdpr.dsar.deadline_missed | `(?i)dsar\s+(?:response|fulfillment)\s+(?:delayed|missed\s+deadline|past\s+(?:...` |
| `unlawful_charge` | high | gdpr.dsar.unlawful_charge | `(?i)dsar\s+(?:fee|charge)\s*[:=]\s*\$?[\d.,]+|charged\s+(?:the\s+)?(?:subject...` |
| `special_category_without_basis` | critical | gdpr.special_category.no_basis | `(?i)(?:processing|collected|stored)\s+(?:health|biometric|genetic|racial|ethn...` |
| `transfer_without_safeguard` | high | gdpr.transfer.no_safeguard | `(?i)transfer\s+(?:to|outside)\s+(?:eu|eea)(?!.{0,400}(?:scc|sccs|standard\s+c...` |
| `breach_notification_late` | high | gdpr.breach.notification_late | `(?i)breach\s+notification\s+(?:delayed|over\s+72\s*hours|past\s+72\s*hours|ou...` |
| `dark_pattern_consent` | high | gdpr.consent.dark_pattern | `(?i)(pre[- ]?ticked|pre[- ]?selected)\s+(?:consent|opt[- ]?in)|consent\s+bund...` |
| `no_dpo_appointed` | medium | gdpr.dpo.not_appointed | `(?i)(?:no|absent)\s+(?:dpo|data\s+protection\s+officer)\s+appointed|dpo\s*[:=...` |
| `erasure_refused_without_basis` | high | gdpr.erasure.refusal_without_basis | `(?i)erasure\s+(?:request\s+)?(?:refused|denied)(?!.{0,400}(?:art\.?\s*17\(3\)...` |
| `missing_dpia` | medium | gdpr.dpia.missing | `(?i)(?:no|absent|not\s+performed)\s+dpia(?!.{0,300}(?:not\s+required|low\s+ri...` |
| `automated_decision_no_disclosure` | medium | gdpr.automated_decision.no_disclosure | `(?i)automated\s+decision[- ]?making(?!.{0,400}(?:logic|significance|consequen...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-gdpr-dsar-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-gdpr-dsar-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-gdpr-dsar-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-gdpr-dsar-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-gdpr-dsar-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_06` | high | grep-gdpr-dsar-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-gdpr-dsar-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-gdpr-dsar-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-gdpr-dsar-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-gdpr-dsar-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-gdpr-dsar-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-gdpr-dsar-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-gdpr-dsar-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-gdpr-dsar-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-gdpr-dsar-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-gdpr-dsar-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-gdpr-dsar-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-gdpr-dsar-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-gdpr-dsar-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-gdpr-dsar-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-gdpr-dsar-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-gdpr-dsar-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-gdpr-dsar-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-gdpr-dsar-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-gdpr-dsar-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-gdpr-dsar-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-gdpr-dsar-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-gdpr-dsar-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-gdpr-dsar-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_30` | high | grep-gdpr-dsar-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-gdpr-dsar-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-gdpr-dsar-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flag...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-gdpr-dsar-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-gdpr-dsar-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-gdpr-dsar-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-gdpr-dsar-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-gdpr-dsar-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-gdpr-dsar-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-gdpr-dsar-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}fla...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-gdpr-dsar-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gdpr.{0,24}dsar.{0,24}red.{0,24}flag...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-gdpr-dsar-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-gdpr-dsar-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-gdpr-dsar-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

