# M&A DD red-flag detectors (6 streams)

*rule-pack* · `rule-pack/grep-ma-dd-red-flags` · v0.1.0 · beta

GREP detectors for financial/legal/IP/customer/HR/tax DD.

| axis | value |
|---|---|
| industry | m_and_a, m_and_a.due_diligence, legal, finance |
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
| `change_of_control_acceleration` | critical | ma.legal.cof_acceleration | `(?i)change[- ]?of[- ]?control\s+(?:acceleration|trigger|provision|clause)` |
| `customer_concentration` | high | ma.customer.concentration | `(?i)customer\s+concentration\s*[:=]?\s*[2-9][0-9]%|single\s+customer\s+(?:>|o...` |
| `non_assignable_customer_contract` | high | ma.customer.non_assignable | `(?i)(?:customer|key)\s+contract\s+(?:not\s+assignable|non[- ]?assignable|requ...` |
| `open_ip_litigation` | critical | ma.ip.open_litigation | `(?i)open\s+(?:ip|patent|trademark|copyright)\s+(?:litigation|lawsuit|infringe...` |
| `open_source_gpl_in_proprietary` | high | ma.ip.copyleft_in_proprietary | `(?i)(?:gpl|agpl|lgpl|copyleft)\s+(?:license|code|library)\s+(?:in|incorporate...` |
| `undisclosed_tax_liability` | critical | ma.tax.undisclosed_liability | `(?i)(?:undisclosed|unrecorded)\s+(?:tax|sales\s+tax|use\s+tax|payroll\s+tax)\...` |
| `nol_section_382_limit` | medium | ma.tax.nol_382 | `(?i)(?:nol|net\s+operating\s+loss)\s+limited\s+by\s+(?:section|§|sec\.?)\s*38...` |
| `key_person_no_retention` | high | ma.hr.key_person_attrition | `(?i)key\s+(?:person|employee|founder|cto|ceo|cfo)(?:\s+is)?\s+(?:not\s+(?:ret...` |
| `equity_overhang_high` | medium | ma.hr.equity_overhang | `(?i)equity\s+overhang\s+(?:>|over)\s+(?:1[5-9]|[2-9][0-9])%|unvested\s+(?:opt...` |
| `accrued_pto_undisclosed` | medium | ma.hr.accrued_pto | `(?i)accrued\s+(?:pto|vacation|holiday)\s+(?:liability\s+)?(?:not\s+(?:on\s+ba...` |
| `warn_act_exposure` | high | ma.hr.warn_exposure | `(?i)\bwarn\s+act\b\s+(?:exposure|noncompliance|violation)|mass\s+layoff\s+wit...` |
| `regulatory_enforcement_action` | critical | ma.legal.regulatory_enforcement | `(?i)(?:open|pending|active)\s+(?:sec|fda|ftc|cftc|finra|cma|cnpd|ico|dpa)\s+(...` |
| `going_concern_qualification` | critical | ma.financial.going_concern | `(?i)going[- ]?concern\s+(?:qualification|doubt|opinion)|auditor.{0,40}going[-...` |
| `working_capital_off_target` | medium | ma.financial.working_capital | `(?i)working\s+capital\s+(?:below|under|short\s+of)\s+(?:target|peg)\s+by\s+\$...` |
| `ebitda_adjustment_aggressive` | medium | ma.financial.ebitda_adjustment | `(?i)(?:add[- ]?back|adjustment)\s+(?:to|from)\s+ebitda\s+(?:>|over)\s+(?:1[5-...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-ma-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-ma-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-ma-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-ma-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-ma-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-ma-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-ma-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-ma-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-ma-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-ma-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-ma-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-ma-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-ma-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-ma-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-ma-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-ma-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-ma-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-ma-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-ma-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-ma-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-ma-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-ma-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-ma-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-ma-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-ma-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-ma-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-ma-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-ma-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-ma-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-ma-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-ma-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-ma-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-ma-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-ma-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,160}(...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-ma-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-ma-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-ma-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,1...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-ma-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{0,16...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-ma-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags)....` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-ma-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ma.{0,24}dd.{0,24}red.{0,24}flags).{...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-ma-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-ma-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-ma-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-ma-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-ma-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-ma-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-ma-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-ma-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-ma-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-ma-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

