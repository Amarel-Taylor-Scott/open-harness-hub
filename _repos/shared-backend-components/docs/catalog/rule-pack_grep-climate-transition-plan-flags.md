# Climate Transition Plan grep flags

*rule-pack* · `rule-pack/grep-climate-transition-plan-flags` · v0.1.0 · experimental

Ten local triage detectors for climate transition plan packets.

| axis | value |
|---|---|
| industry | climate, esg.csrd |
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
| `net_zero_target` | critical | climate_transition_plan.net_zero_target | `(?i)net.{0,36}zero.{0,36}target` |
| `scope_3_missing` | critical | climate_transition_plan.scope_3_missing | `(?i)scope.{0,36}3.{0,36}missing` |
| `offset_reliance` | high | climate_transition_plan.offset_reliance | `(?i)offset.{0,36}reliance` |
| `capex_alignment` | high | climate_transition_plan.capex_alignment | `(?i)capex.{0,36}alignment` |
| `interim_target` | high | climate_transition_plan.interim_target | `(?i)interim.{0,36}target` |
| `transition_risk` | high | climate_transition_plan.transition_risk | `(?i)transition.{0,36}risk` |
| `board_oversight` | medium | climate_transition_plan.board_oversight | `(?i)board.{0,36}oversight` |
| `scenario_analysis` | medium | climate_transition_plan.scenario_analysis | `(?i)scenario.{0,36}analysis` |
| `greenwashing` | medium | climate_transition_plan.greenwashing | `(?i)greenwashing` |
| `assurance_gap` | medium | climate_transition_plan.assurance_gap | `(?i)assurance.{0,36}gap` |
| `scale_expansion_v1_critical_signal_01` | high | grep-climate-transition-plan-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}climate.{0,24}transition.{0,24}plan.{...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-climate-transition-plan-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,24}f...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-climate-transition-plan-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-climate-transition-plan-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-climate-transition-plan-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-climate-transition-plan-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,2...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-climate-transition-plan-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}climate.{0,24}transition.{0,24}plan...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-climate-transition-plan-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}climate.{0,24}transition.{0,24}plan....` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-climate-transition-plan-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}climate.{0,24}transition.{0,24}plan.{...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-climate-transition-plan-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,24}f...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-climate-transition-plan-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-climate-transition-plan-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-climate-transition-plan-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-climate-transition-plan-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,2...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-climate-transition-plan-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}climate.{0,24}transition.{0,24}plan...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-climate-transition-plan-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}climate.{0,24}transition.{0,24}plan....` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-climate-transition-plan-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}climate.{0,24}transition.{0,24}plan.{...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-climate-transition-plan-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,24}f...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-climate-transition-plan-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-climate-transition-plan-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-climate-transition-plan-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-climate-transition-plan-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,2...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-climate-transition-plan-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}climate.{0,24}transition.{0,24}plan...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-climate-transition-plan-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}climate.{0,24}transition.{0,24}plan....` |
| `scale_expansion_v1_critical_signal_25` | high | grep-climate-transition-plan-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}climate.{0,24}transition.{0,24}plan.{...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-climate-transition-plan-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,24}f...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-climate-transition-plan-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-climate-transition-plan-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-climate-transition-plan-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-climate-transition-plan-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,2...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-climate-transition-plan-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}climate.{0,24}transition.{0,24}plan...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-climate-transition-plan-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}climate.{0,24}transition.{0,24}plan....` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-climate-transition-plan-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}climate.{0,24}transition.{0,24}plan.{...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-climate-transition-plan-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,24}f...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-climate-transition-plan-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-climate-transition-plan-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-climate-transition-plan-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-climate-transition-plan-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}climate.{0,24}transition.{0,24}plan.{0,2...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-climate-transition-plan-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}climate.{0,24}transition.{0,24}plan...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-climate-transition-plan-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}climate.{0,24}transition.{0,24}plan....` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-climate-transition-plan-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-climate-transition-plan-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-climate-transition-plan-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-climate-transition-plan-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-climate-transition-plan-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-climate-transition-plan-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-climate-transition-plan-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

