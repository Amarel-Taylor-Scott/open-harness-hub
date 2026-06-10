# Statute / regulation ambiguity GREP red-flag detectors

*rule-pack* · `rule-pack/grep-statute-ambiguity-flags` · v0.1.0 · experimental

Regex heuristics that fire on the most common drafting failures in
statutes, regulations, ordinances, and agency rules:

 - vague qualifiers ("reasonable", "appropriate", "as soon as
   practicable", "substantial")
 - undefined enumerations with no closing catch-all
 - broken cross-references ("§X" with no §X in the same act)
 - retroactivity ambiguity ("applies to all" without effective
   date scoping)
 - missing severability / effective-date markers
 - circular definitions (a defined term that uses the same word in
   its own definition)
 - scope-creep verbs ("includes but is not limited to" inside
   a definition)
 - shall/may/will inconsistency
 - English-only "as defined elsewhere" forward-references

FAST first-pass heuristics — they flag passages for the
`persona/legal-clarity-analyst` to interpret, never determine
interpretation themselves.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government, government.regulatory |
| capability | safety_gating, classification, extraction |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `vague_qualifier_reasonable` | medium | drafting.vague_qualifier | `(?i)\b(reasonable|reasonably|reasonableness)\b` |
| `vague_qualifier_appropriate` | medium | drafting.vague_qualifier | `(?i)\b(appropriate|appropriately|as appropriate)\b` |
| `vague_qualifier_practicable` | medium | drafting.vague_qualifier | `(?i)\b(practicable|as soon as practicable|reasonably practicable|insofar as p...` |
| `vague_qualifier_substantial` | medium | drafting.vague_qualifier | `(?i)\b(substantial|substantially|in substantial part|materially)\b` |
| `vague_qualifier_undue` | medium | drafting.vague_qualifier | `(?i)\b(undue|undue hardship|undue burden|unreasonable)\b` |
| `open_enumeration_includes_but` | medium | drafting.open_enumeration | `(?i)\b(includes? but (is|are) not limited to|including without limitation|suc...` |
| `shall_may_inconsistency` | low | drafting.modal_verb_consistency | `(?i)\b(shall|may|must|will|should)\b.{0,200}?\b(shall|may|must|will|should)\b` |
| `broken_section_xref` | low | drafting.cross_reference_to_verify | `(?i)\b(section|subsection|paragraph|clause|art\.?|article)\s+\d+(\([a-z0-9]+\))*` |
| `retroactivity_ambiguity` | high | drafting.retroactivity_ambiguity | `(?i)\bapplies?\s+to\s+(all|any)\s+(persons?|transactions?|acts?|conduct|filin...` |
| `missing_effective_date_marker` | high | drafting.missing_effective_date | `(?i)\b(this (act|chapter|section|subchapter|title|regulation|rule))\b(?!.{0,5...` |
| `missing_severability_marker` | medium | drafting.severability_check | `(?i)\bif (any|a) (provision|section|subsection|clause)\b(?!.{0,200}\b(invalid...` |
| `circular_definition_marker` | high | drafting.circular_definition | `(?i)"([A-Z][a-z]+)"\\s+means.{0,200}\\b\\1\\b` |
| `forward_reference` | medium | drafting.forward_reference | `(?i)\bas defined (elsewhere|herein|below|hereinafter|in this (chapter|title|s...` |
| `deadline_unclear` | medium | drafting.deadline_unclear | `(?i)\b(promptly|immediately|forthwith|without delay|as soon as)\b` |
| `delegation_open` | low | drafting.delegation_to_verify | `(?i)\b(the (secretary|administrator|commissioner|director|agency|authority)) ...` |
| `scope_creep_includes` | high | drafting.definitional_scope_creep | `(?i)"[A-Z][a-z]+"\\s+(means|shall mean)\\s+.{0,200}\\b(and includes any other...` |
| `unconstitutional_red_flag_prior_restraint` | critical | constitutional.prior_restraint_risk | `(?i)\b(may not (be |)?(publish|distribute|broadcast|disseminate|post)|prohibi...` |
| `due_process_no_hearing` | critical | constitutional.due_process_risk | `(?i)\b(without (notice|a hearing|opportunity to be heard|judicial review)|sum...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-statute-ambiguity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-statute-ambiguity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-statute-ambiguity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-statute-ambiguity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-statute-ambiguity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-statute-ambiguity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-statute-ambiguity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-statute-ambiguity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-statute-ambiguity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_10` | high | grep-statute-ambiguity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-statute-ambiguity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-statute-ambiguity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-statute-ambiguity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-statute-ambiguity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-statute-ambiguity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-statute-ambiguity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-statute-ambiguity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-statute-ambiguity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-statute-ambiguity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-statute-ambiguity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-statute-ambiguity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-statute-ambiguity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-statute-ambiguity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-statute-ambiguity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-statute-ambiguity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_26` | high | grep-statute-ambiguity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-statute-ambiguity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-statute-ambiguity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-statute-ambiguity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-statute-ambiguity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-statute-ambiguity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-statute-ambiguity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-statute-ambiguity-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-statute-ambiguity-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-statute-ambiguity-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-statute-ambiguity-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-statute-ambiguity-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-statute-ambiguity-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-statute-ambiguity-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-statute-ambiguity-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}statute.{0,24}ambiguity.{0,24}flags)...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-statute-ambiguity-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-statute-ambiguity-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-statute-ambiguity-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-statute-ambiguity-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-statute-ambiguity-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-statute-ambiguity-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-statute-ambiguity-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

