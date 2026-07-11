# Commercial contract red-flag detectors

*rule-pack* · `rule-pack/grep-contract-red-flags` · v0.1.0 · beta

GREP detectors for the 10 highest-leverage contract red-flag
patterns: uncapped indemnity, unlimited liability, pre-existing
IP assignment, unilateral termination, asymmetric caps, missing
DPA, missing audit rights, missing anti-bribery, change-of-
control without consent, narrow force-majeure.

These trigger reviews — they are not definitive flags. Pair with
`pipeline/contract-clause-review` for full grading.

| axis | value |
|---|---|
| industry | legal, legal.contract, legal.compliance |
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
| `uncapped_indemnity` | critical | legal.uncapped_indemnity | `(?is)indemnif\w*.{0,200}(without limitation|unlimited|no cap|uncapped|any and...` |
| `unlimited_liability` | critical | legal.unlimited_liability | `(?is)(liability|liable)\s+(?:shall be |is )?(?:unlimited|without limit|withou...` |
| `ip_assignment_preexisting` | critical | legal.ip_assignment_preexisting | `(?is)assign(?:s|ment)?\s+(?:to\s+\w+\s+)?(?:all|any)\s+(?:right.{0,30}intelle...` |
| `termination_short_notice` | high | legal.termination_short_notice | `(?is)terminat\w*\s+(?:for convenience|at will|at any time)\s+upon\s+(?:[1-9](...` |
| `no_audit_rights` | high | legal.no_audit_rights | `(?is)(no audit rights|customer may not audit|audit (?:is )?(?:prohibited|not ...` |
| `missing_anti_bribery_warranty` | high | legal.missing_anti_bribery | `(?is)\b(no anti[- ]?bribery|no FCPA|no sanctions (?:representation|warranty))...` |
| `free_assignment` | high | legal.free_assignment | `(?is)may (?:freely )?assign.{0,80}(?:without|no)\s+(?:notice|consent|approval...` |
| `force_majeure_narrow` | medium | legal.force_majeure_narrow | `(?is)force majeure.{0,300}\bonly\b|force majeure.{0,300}(acts of god and war|...` |
| `missing_dpa` | critical | legal.missing_dpa | `(?is)(process|processing).{0,40}personal data(?!.{0,800}(DPA|data processing ...` |
| `asymmetric_cap` | critical | legal.asymmetric_cap | `(?is)Vendor.{0,200}(liability|liable).{0,100}\$?\s*[\d,]+\s+(?:in aggregate)?...` |
| `auto_renewal_short_window` | medium | legal.auto_renewal_short_window | `(?is)auto[- ]?renew\w*.{0,100}(unless.{0,40}notice.{0,40}(\d{1,2})\s*days)(?:...` |
| `exclusivity_perpetual` | high | legal.perpetual_exclusivity | `(?is)(exclusive|sole)\s+(?:supplier|provider|distributor).{0,200}perpetual|pe...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-contract-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-contract-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-contract-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-contract-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-contract-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-contract-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-contract-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-contract-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-contract-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-contract-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-contract-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-contract-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-contract-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-contract-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-contract-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-contract-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-contract-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-contract-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-contract-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-contract-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-contract-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-contract-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-contract-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-contract-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-contract-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-contract-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-contract-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-contract-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-contract-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-contract-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-contract-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-contract-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-contract-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-contract-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-contract-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-contract-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-contract-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-contract-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-contract-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-contract-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}contract.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-contract-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-contract-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-contract-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-contract-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-contract-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-contract-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-contract-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-contract-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-contract-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-contract-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

