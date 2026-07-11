# Cold Chain Pharma Release grep flags

*rule-pack* · `rule-pack/grep-cold-chain-pharma-release-flags` · v0.1.0 · experimental

Ten local triage detectors for cold chain pharma release packets.

| axis | value |
|---|---|
| industry | logistics.cold_chain, pharma.gxp |
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
| `temperature_excursion` | critical | cold_chain_pharma_release.temperature_excursion | `(?i)temperature.{0,36}excursion` |
| `QA_release` | critical | cold_chain_pharma_release.QA_release | `(?i)QA.{0,36}release` |
| `stability_data` | high | cold_chain_pharma_release.stability_data | `(?i)stability.{0,36}data` |
| `lane_qualification` | high | cold_chain_pharma_release.lane_qualification | `(?i)lane.{0,36}qualification` |
| `logger_missing` | high | cold_chain_pharma_release.logger_missing | `(?i)logger.{0,36}missing` |
| `GDP_custody` | high | cold_chain_pharma_release.GDP_custody | `(?i)GDP.{0,36}custody` |
| `shipment_quarantine` | medium | cold_chain_pharma_release.shipment_quarantine | `(?i)shipment.{0,36}quarantine` |
| `MKT_calculation` | medium | cold_chain_pharma_release.MKT_calculation | `(?i)MKT.{0,36}calculation` |
| `calibration_expired` | medium | cold_chain_pharma_release.calibration_expired | `(?i)calibration.{0,36}expired` |
| `deviation_open` | medium | cold_chain_pharma_release.deviation_open | `(?i)deviation.{0,36}open` |
| `scale_expansion_v1_critical_signal_01` | high | grep-cold-chain-pharma-release-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}r...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}release...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}re...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-cold-chain-pharma-release-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-cold-chain-pharma-release-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rele...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}r...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-cold-chain-pharma-release-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}release...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-cold-chain-pharma-release-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}re...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rele...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-cold-chain-pharma-release-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-cold-chain-pharma-release-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}r...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}release...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-cold-chain-pharma-release-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}re...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-cold-chain-pharma-release-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rele...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-cold-chain-pharma-release-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}r...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-cold-chain-pharma-release-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}release...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}re...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-cold-chain-pharma-release-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rele...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-cold-chain-pharma-release-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}r...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}release...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-cold-chain-pharma-release-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-cold-chain-pharma-release-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}re...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rel...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}rele...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-cold-chain-pharma-release-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-cold-chain-pharma-release-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}cold.{0,24}chain.{0,24}pharma.{0,24}...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-cold-chain-pharma-release-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-cold-chain-pharma-release-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-cold-chain-pharma-release-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

