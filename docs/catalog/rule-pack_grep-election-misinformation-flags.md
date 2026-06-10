# Election misinformation / disinformation / deepfake detectors

*rule-pack* · `rule-pack/grep-election-misinformation-flags` · v0.1.0 · beta

Heuristic GREP detectors for common election-misinformation patterns.

| axis | value |
|---|---|
| industry | election_integrity, media, media.factcheck |
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
| `wrong_polling_place_claim` | critical | election.wrong_polling_place | `(?i)(?:voting\s+location|polling\s+place|vote\s+at)\s+(?:changed|moved|reloca...` |
| `wrong_election_date_claim` | critical | election.wrong_date | `(?i)(?:election\s+(?:date|day)|vote)\s+(?:moved|postponed|changed)\s+to\s+(?:...` |
| `fake_ballot_instruction` | high | election.fake_ballot_instruction | `(?i)(?:to\s+vote\s+(?:for|against)|mark\s+ballot)\s+(?:democrat|republican|li...` |
| `voter_id_misinformation` | high | election.voter_id_misinformation | `(?i)(?:must\s+(?:have|bring)|required)\s+(?:photo\s+id|driver'?s?\s+license|p...` |
| `deepfake_component_keyword` | high | election.deepfake_component | `(?i)(?:lip[- ]?sync\s+(?:off|mismatched)|c2pa\s+(?:missing|absent|stripped)|c...` |
| `coordinated_inauthentic_behavior` | high | election.cib | `(?i)(?:coordinated\s+inauthentic\s+behavior|botnet|sockpuppet\s+network|astro...` |
| `voter_intimidation_text` | critical | election.voter_intimidation | `(?i)(?:do\s+not\s+vote\s+if|stay\s+home|police\s+will\s+be|ice\s+(?:agents?\s...` |
| `fake_official_seal_claim` | medium | election.fake_authority | `(?i)(?:official\s+(?:state|county)\s+election|secretary\s+of\s+state\s+notice...` |
| `incorrect_eligibility_claim` | high | election.fake_eligibility | `(?i)(?:cannot\s+vote|ineligible)\s+if\s+(?:you\s+(?:rent|are\s+a\s+felon|are\...` |
| `voter_roll_pii_in_public` | critical | election.voter_roll_pii_leak | `(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)` |
| `scale_expansion_v1_critical_signal_01` | high | grep-election-misinformation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}election.{0,24}misinformation.{0,24}f...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-election-misinformation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flags)....` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-election-misinformation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-election-misinformation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fl...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-election-misinformation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-election-misinformation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flag...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-election-misinformation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}election.{0,24}misinformation.{0,24...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-election-misinformation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}election.{0,24}misinformation.{0,24}...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-election-misinformation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}election.{0,24}misinformation.{0,24}f...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-election-misinformation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flags)....` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-election-misinformation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-election-misinformation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fl...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-election-misinformation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-election-misinformation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flag...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-election-misinformation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}election.{0,24}misinformation.{0,24...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-election-misinformation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}election.{0,24}misinformation.{0,24}...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-election-misinformation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}election.{0,24}misinformation.{0,24}f...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-election-misinformation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flags)....` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-election-misinformation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-election-misinformation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fl...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-election-misinformation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-election-misinformation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flag...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-election-misinformation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}election.{0,24}misinformation.{0,24...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-election-misinformation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}election.{0,24}misinformation.{0,24}...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-election-misinformation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}election.{0,24}misinformation.{0,24}f...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-election-misinformation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flags)....` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-election-misinformation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-election-misinformation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fl...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-election-misinformation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-election-misinformation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flag...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-election-misinformation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}election.{0,24}misinformation.{0,24...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-election-misinformation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}election.{0,24}misinformation.{0,24}...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-election-misinformation-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}election.{0,24}misinformation.{0,24}f...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-election-misinformation-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flags)....` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-election-misinformation-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-election-misinformation-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}election.{0,24}misinformation.{0,24}fl...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-election-misinformation-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}fla...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-election-misinformation-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}election.{0,24}misinformation.{0,24}flag...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-election-misinformation-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}election.{0,24}misinformation.{0,24...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-election-misinformation-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}election.{0,24}misinformation.{0,24}...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-election-misinformation-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-election-misinformation-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-election-misinformation-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-election-misinformation-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-election-misinformation-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-election-misinformation-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-election-misinformation-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-election-misinformation-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-election-misinformation-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-election-misinformation-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

