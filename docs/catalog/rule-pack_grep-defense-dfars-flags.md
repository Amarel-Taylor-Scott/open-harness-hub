# Defense DFARS + CMMC + counterfeit-parts red-flag detectors

*rule-pack* · `rule-pack/grep-defense-dfars-flags` · v0.1.0 · beta

GREP detectors for DFARS / CMMC / SAE AS5553 / Section 889 / SAM exclusion.

| axis | value |
|---|---|
| industry | defense, defense.dfars, defense.counterfeit_parts, defense.cmmc |
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
| `no_cmmc_level_assigned` | critical | defense.cmmc.no_level | `(?i)cmmc\s+(?:level\s+)?(?:not\s+(?:assigned|determined|specified)|tbd|n[\.\/...` |
| `dfars_7012_breach_unreported` | critical | defense.cyber.dfars_7012_breach | `(?i)(?:cyber\s+(?:incident|breach))\s+(?:not\s+reported|past\s+72\s+hours)|di...` |
| `section_889_telecom` | critical | defense.sec_889.covered_telecom | `(?i)(?:huawei|zte|hytera|hikvision|dahua)\s+(?:equipment|gear|hardware|compon...` |
| `counterfeit_part_indicator` | critical | defense.counterfeit_parts.indicator | `(?i)(?:counterfeit|suspect[- ]?counterfeit|unmarked|unauthorized\s+distributo...` |
| `sam_exclusion_hit` | critical | defense.sam.exclusion | `(?i)sam(?:\.gov)?\s+(?:exclusion|debarred|suspended)\s+(?:list|hit)|excluded\...` |
| `itar_unlicensed_transfer` | critical | defense.itar.unlicensed | `(?i)itar\s+(?:controlled\s+)?(?:technical\s+data|defense\s+article)\s+(?:tran...` |
| `buy_american_noncompliance` | high | defense.buy_american | `(?i)buy\s+american\s+(?:noncompliance|violation|exception\s+not\s+claimed)|fo...` |
| `nist_800_171_gap` | high | defense.nist_800_171.gap | `(?i)nist\s+800[- ]?171\s+(?:control|requirement)\s+(?:gap|missing|not\s+imple...` |
| `supply_chain_no_traceability` | high | defense.supply_chain.no_traceability | `(?i)supply[- ]?chain\s+(?:traceability|provenance)\s+(?:not\s+(?:established|...` |
| `cui_marking_missing` | medium | defense.cui.marking_missing | `(?i)controlled\s+unclassified\s+information|\bcui\b(?!.{0,200}(?:properly\s+m...` |
| `as5553_no_inspection` | high | defense.counterfeit_parts.no_as5553 | `(?i)(?:as5553|as6081|sae\s+aerospace\s+standard)\s+(?:not\s+followed|gap)|ele...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-defense-dfars-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-defense-dfars-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-defense-dfars-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-defense-dfars-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-defense-dfars-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-defense-dfars-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-defense-dfars-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-defense-dfars-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-defense-dfars-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-defense-dfars-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-defense-dfars-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-defense-dfars-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-defense-dfars-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-defense-dfars-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-defense-dfars-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-defense-dfars-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-defense-dfars-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-defense-dfars-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-defense-dfars-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-defense-dfars-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-defense-dfars-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-defense-dfars-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-defense-dfars-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-defense-dfars-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-defense-dfars-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-defense-dfars-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-defense-dfars-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-defense-dfars-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-defense-dfars-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-defense-dfars-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-defense-dfars-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-defense-dfars-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-defense-dfars-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-defense-dfars-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-defense-dfars-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-defense-dfars-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-defense-dfars-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-defense-dfars-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-defense-dfars-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-defense-dfars-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}defense.{0,24}dfars.{0,24}flags).{0,...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-defense-dfars-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-defense-dfars-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-defense-dfars-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-defense-dfars-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-defense-dfars-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-defense-dfars-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-defense-dfars-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-defense-dfars-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-defense-dfars-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-defense-dfars-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

