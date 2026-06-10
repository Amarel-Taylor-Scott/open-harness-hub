# Transfer-pricing red-flag detectors (OECD / §482 / BEPS)

*rule-pack* · `rule-pack/grep-transfer-pricing-flags` · v0.1.0 · beta

Detectors for transfer-pricing risk.

| axis | value |
|---|---|
| industry | tax, tax.transfer_pricing, finance |
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
| `no_benchmarking_study` | critical | tax.tp.no_benchmarking | `(?i)(?:no|absent|missing)\s+benchmarking\s+(?:study|analysis)|comparables\s+(...` |
| `embedded_royalty_no_ip` | high | tax.tp.embedded_royalty | `(?i)(?:embedded\s+royalty|hidden\s+royalty)\s+(?:without|absent)\s+(?:ip\s+(?...` |
| `captive_insurance_no_risk` | high | tax.tp.captive_no_risk | `(?i)captive\s+insurance(?:\s+(?:company|reinsurance))?(?!.{0,200}(?:risk\s+tr...` |
| `loss_making_lrd` | critical | tax.tp.loss_making_lrd | `(?i)(?:limited[- ]?risk\s+distributor|lrd)\s+(?:loss[- ]?making|negative\s+ma...` |
| `cash_pool_below_arm_length` | high | tax.tp.cash_pool_interest | `(?i)cash[- ]?pool(?:ing)?\s+(?:interest|rate)\s+(?:below\s+arm'?s[- ]?length|...` |
| `no_master_file` | high | tax.tp.no_master_file | `(?i)(?:no|absent|missing)\s+master\s+file|master\s+file\s+(?:not\s+(?:prepare...` |
| `no_local_file` | high | tax.tp.no_local_file | `(?i)(?:no|absent|missing)\s+local\s+file|local\s+file\s+(?:not\s+(?:prepared|...` |
| `no_cbcr` | high | tax.tp.no_cbcr | `(?i)country[- ]?by[- ]?country\s+report(?:ing)?\s+(?:not\s+(?:prepared|filed)...` |
| `hard_to_value_intangible` | high | tax.tp.htvi | `(?i)(?:hard[- ]?to[- ]?value\s+intangible|htvi)(?!.{0,300}(?:ex[- ]?post\s+ad...` |
| `cca_no_balancing_payment` | medium | tax.tp.cca_imbalanced | `(?i)cost\s+contribution\s+arrangement\s+(?:without\s+balancing\s+payment|imba...` |
| `pillar_two_etr_below_15` | critical | tax.pillar_two.etr_below_15 | `(?i)(?:effective\s+tax\s+rate|etr)\s+(?:below|under)\s+15\s*%(?!.{0,200}(?:su...` |
| `permanent_establishment_risk` | high | tax.tp.pe_risk | `(?i)(?:dependent\s+agent|fixed\s+place\s+of\s+business|home[- ]?office\s+pe)\...` |
| `fin_tx_no_credit_rating` | medium | tax.tp.fin_tx_no_rating | `(?i)(?:intercompany|related[- ]?party)\s+(?:loan|guarantee|credit\s+facility)...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-transfer-pricing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-transfer-pricing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-transfer-pricing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-transfer-pricing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-transfer-pricing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-transfer-pricing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,1...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-transfer-pricing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-transfer-pricing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)....` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-transfer-pricing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-transfer-pricing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-transfer-pricing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-transfer-pricing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-transfer-pricing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-transfer-pricing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,1...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-transfer-pricing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-transfer-pricing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)....` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-transfer-pricing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-transfer-pricing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-transfer-pricing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-transfer-pricing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-transfer-pricing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-transfer-pricing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,1...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-transfer-pricing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-transfer-pricing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)....` |
| `scale_expansion_v1_critical_signal_25` | high | grep-transfer-pricing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-transfer-pricing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-transfer-pricing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-transfer-pricing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-transfer-pricing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-transfer-pricing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,1...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-transfer-pricing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-transfer-pricing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)....` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-transfer-pricing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-transfer-pricing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-transfer-pricing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-transfer-pricing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-transfer-pricing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-transfer-pricing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}transfer.{0,24}pricing.{0,24}flags).{0,1...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-transfer-pricing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-transfer-pricing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}transfer.{0,24}pricing.{0,24}flags)....` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-transfer-pricing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-transfer-pricing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-transfer-pricing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-transfer-pricing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-transfer-pricing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-transfer-pricing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-transfer-pricing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-transfer-pricing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-transfer-pricing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-transfer-pricing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

