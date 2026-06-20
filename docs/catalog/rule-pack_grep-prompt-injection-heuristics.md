# Prompt-injection heuristic detectors

*rule-pack* · `rule-pack/grep-prompt-injection-heuristics` · v0.1.0 · beta

Heuristic regex patterns that flag likely prompt-injection attempts
in input, retrieved documents, or tool results. Inspired by garak
probe families (`promptinject`, `latentinjection`, `ansiescape`,
`encoding`, `dan`) and LLM Guard's `PromptInjection` scanner.

These are FAST FIRST-PASS heuristics; pair with a small-model
classifier (`processor/prompt-injection-detector`) for robust
defense. False positives are common; use to TRIGGER a review or
paraphrase, not to block outright.

| axis | value |
|---|---|
| industry | security, ai, cross_industry |
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
| `ignore_previous_instructions` | high | prompt_injection.override | `(?i)ignore (the (?:previous|prior|above) )?(?:instructions|prompt|message|dir...` |
| `you_are_now_role_override` | medium | prompt_injection.role_play | `(?i)you (?:are|will be|must be) (?:now |henceforth )?(?:a|an|the) [a-z]+ (?:t...` |
| `dan_jailbreak` | high | prompt_injection.jailbreak | `(?i)\b(DAN|do anything now|developer mode|jailbreak|liberate)\b` |
| `system_prompt_leak_request` | high | prompt_injection.leak | `(?i)(repeat|reveal|tell me|show me|print|output) (the |your )?(?:system promp...` |
| `encoding_attack_base64` | high | prompt_injection.encoding | `(?i)decode (the |this )?base64.{0,40}?(then|and) (execute|follow|do|perform)` |
| `ansi_escape_injection` | high | prompt_injection.terminal_escape | `\x1b\[[0-9;]*[A-Za-z]` |
| `invisible_unicode_tag_chars` | critical | prompt_injection.invisible_unicode | `[\u{E0000}-\u{E007F}]` |
| `zero_width_characters` | medium | prompt_injection.steganography | `[\u200b\u200c\u200d\u2060\ufeff]` |
| `indirect_injection_markdown` | medium | prompt_injection.markdown | `(?i)\[.*?\]\(.*?(?:ignore|reveal|system prompt|disregard).*?\)` |
| `tool_invocation_in_doc` | high | prompt_injection.tool_invocation | `(?i)<tool[\s_-]?(?:call|use)>|\{\{\s*tool\s*\(.*\)\s*\}\}` |
| `grandma_attack` | high | prompt_injection.social_engineering | `(?i)(grandma|grandmother) (used to|would) (tell|recite|sing) (me )?(.{0,40}?)...` |
| `instruction_injection_keyword_list` | high | prompt_injection.override | `(?i)(ignore|disregard|forget|override) (above|previous|all) (instructions|rul...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-prompt-injection-heuristics.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}prompt.{0,24}injection.{0,24}heuristi...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-prompt-injection-heuristics.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics).{0...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-prompt-injection-heuristics.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-prompt-injection-heuristics.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristic...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-prompt-injection-heuristics.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-prompt-injection-heuristics.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics)...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-prompt-injection-heuristics.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}prompt.{0,24}injection.{0,24}heuris...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-prompt-injection-heuristics.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}prompt.{0,24}injection.{0,24}heurist...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-prompt-injection-heuristics.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}prompt.{0,24}injection.{0,24}heuristi...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-prompt-injection-heuristics.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics).{0...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-prompt-injection-heuristics.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-prompt-injection-heuristics.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristic...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-prompt-injection-heuristics.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-prompt-injection-heuristics.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics)...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-prompt-injection-heuristics.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}prompt.{0,24}injection.{0,24}heuris...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-prompt-injection-heuristics.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}prompt.{0,24}injection.{0,24}heurist...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-prompt-injection-heuristics.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}prompt.{0,24}injection.{0,24}heuristi...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-prompt-injection-heuristics.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics).{0...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-prompt-injection-heuristics.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-prompt-injection-heuristics.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristic...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-prompt-injection-heuristics.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-prompt-injection-heuristics.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics)...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-prompt-injection-heuristics.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}prompt.{0,24}injection.{0,24}heuris...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-prompt-injection-heuristics.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}prompt.{0,24}injection.{0,24}heurist...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-prompt-injection-heuristics.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}prompt.{0,24}injection.{0,24}heuristi...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-prompt-injection-heuristics.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics).{0...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-prompt-injection-heuristics.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-prompt-injection-heuristics.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristic...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-prompt-injection-heuristics.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-prompt-injection-heuristics.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics)...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-prompt-injection-heuristics.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}prompt.{0,24}injection.{0,24}heuris...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-prompt-injection-heuristics.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}prompt.{0,24}injection.{0,24}heurist...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-prompt-injection-heuristics.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}prompt.{0,24}injection.{0,24}heuristi...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-prompt-injection-heuristics.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics).{0...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-prompt-injection-heuristics.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-prompt-injection-heuristics.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}prompt.{0,24}injection.{0,24}heuristic...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-prompt-injection-heuristics.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-prompt-injection-heuristics.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}prompt.{0,24}injection.{0,24}heuristics)...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-prompt-injection-heuristics.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}prompt.{0,24}injection.{0,24}heuris...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-prompt-injection-heuristics.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}prompt.{0,24}injection.{0,24}heurist...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-prompt-injection-heuristics.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-prompt-injection-heuristics.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-prompt-injection-heuristics.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-prompt-injection-heuristics.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-prompt-injection-heuristics.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-prompt-injection-heuristics.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-prompt-injection-heuristics.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

