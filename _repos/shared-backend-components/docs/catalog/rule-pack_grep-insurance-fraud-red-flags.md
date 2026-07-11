# Insurance claim fraud red-flag detectors (NAIC + CAIF)

*rule-pack* · `rule-pack/grep-insurance-fraud-red-flags` · v0.1.0 · beta

GREP detectors for the highest-leverage insurance-claim fraud
red flags drawn from NAIC fraud-fighter handbook + Coalition
Against Insurance Fraud indicators. Pair with
`pipeline/insurance-claim-review`.

| axis | value |
|---|---|
| industry | insurance, insurance.claims, insurance.fraud, finance |
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
| `recent_coverage_change` | critical | insurance.fraud.recent_coverage_change | `(?i)(coverage\s+(?:increased|upgraded|added|amended)|policy\s+(?:increased|up...` |
| `loss_at_renewal` | high | insurance.fraud.loss_at_renewal | `(?i)loss\s+(?:occurred|reported)\s+(?:within|less than)\s+\d{1,3}\s+days?\s+(...` |
| `claimant_on_fraud_watchlist` | critical | insurance.fraud.claimant_watchlist | `(?i)claimant\s+on\s+(?:internal\s+)?fraud\s+(?:watch[- ]?list|flag\s+list)|pr...` |
| `conflicting_witness` | high | insurance.fraud.conflicting_witness | `(?i)witness\s+statements?\s+(?:conflict|contradict|inconsistent|disagree)|two...` |
| `photos_predate_loss` | critical | insurance.fraud.photo_metadata | `(?i)photos?\s+(?:pre[- ]?date|predating|taken before|exif\s+date\s+(?:before|...` |
| `inflated_invoice` | high | insurance.fraud.inflated_invoice | `(?i)(?:repair|invoice|estimate)\s+(?:significantly\s+)?(?:above|exceeds)\s+(?...` |
| `shop_on_flag_list` | high | insurance.fraud.provider_flagged | `(?i)(?:repair\s+shop|provider|vendor)\s+(?:on|flagged on)\s+(?:internal\s+)?(...` |
| `missing_police_report` | medium | insurance.fraud.no_police_report | `(?i)(?:no|absent|not\s+filed|n[\.\/]?a)\s+police\s+report(?!.{0,120}(minor|un...` |
| `claimant_relationship_to_witness` | medium | insurance.fraud.witness_relationship | `(?i)witness\s+(?:is|was)\s+(?:family|spouse|relative|business partner|employe...` |
| `ssn_in_claim_body` | high | phi.ssn_unredacted | `(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)` |
| `phantom_damage_pattern` | critical | insurance.fraud.phantom_damage | `(?i)damage\s+(?:not\s+consistent|inconsistent)\s+with\s+(?:reported|alleged)\...` |
| `multiple_claims_short_window` | high | insurance.fraud.serial_claims | `(?i)(\d+|\bmultiple\b|several)\s+(?:prior\s+)?claims?\s+(?:filed|submitted)\s...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-insurance-fraud-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-insurance-fraud-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-insurance-fraud-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-insurance-fraud-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-insurance-fraud-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-insurance-fraud-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}fl...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-insurance-fraud-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-insurance-fraud-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,2...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-insurance-fraud-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-insurance-fraud-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-insurance-fraud-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-insurance-fraud-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-insurance-fraud-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-insurance-fraud-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}fl...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-insurance-fraud-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-insurance-fraud-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,2...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-insurance-fraud-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-insurance-fraud-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-insurance-fraud-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-insurance-fraud-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-insurance-fraud-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-insurance-fraud-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}fl...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-insurance-fraud-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-insurance-fraud-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,2...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-insurance-fraud-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-insurance-fraud-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-insurance-fraud-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-insurance-fraud-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-insurance-fraud-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-insurance-fraud-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}fl...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-insurance-fraud-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-insurance-fraud-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,2...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-insurance-fraud-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-insurance-fraud-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}flags...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-insurance-fraud-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-insurance-fraud-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-insurance-fraud-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}f...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-insurance-fraud-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,24}fl...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-insurance-fraud-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-insurance-fraud-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}insurance.{0,24}fraud.{0,24}red.{0,2...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-insurance-fraud-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-insurance-fraud-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-insurance-fraud-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

