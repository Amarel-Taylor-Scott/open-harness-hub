# Wikipedia article quality red-flag detectors (NPOV / V / OR / promo)

*rule-pack* · `rule-pack/grep-wikipedia-quality-flags` · v0.1.0 · experimental

Regex heuristics catching the most common WP:NPOV / WP:V / WP:OR /
WP:PROMO failure patterns in Wikipedia article text:

 - editorial voice ("clearly", "obviously", "fortunately")
 - weasel attributions ("some say", "critics argue", "many believe")
 - peacock terms ("renowned", "legendary", "world-class")
 - loaded labels ("regime", "cult", "denialist", "terrorist")
 - hedging markers ("may", "could", "is said to", "reportedly")
 - promotional phrasing ("award-winning", "pioneering", "industry-
   leading", "first-of-its-kind")
 - synth markers (sentence-initial "Therefore", "Thus", "As a
   result" without citation)
 - {{citation needed}} markers already present
 - primary-source dump indicators (long quote blocks)
 - self-published source patterns ("according to [person's] blog")

FAST first-pass heuristics — they flag passages for the
`persona/wikipedia-quality-reviewer` to evaluate; they do not
determine policy violation.

| axis | value |
|---|---|
| industry | media, media.editorial, media.factcheck |
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
| `editorial_voice_clearly` | medium | npov.editorial_voice | `(?i)\b(clearly|obviously|undoubtedly|certainly|of course|naturally)\b` |
| `editorial_voice_value_judgment` | medium | npov.editorial_voice | `(?i)\b(fortunately|unfortunately|sadly|tragically|happily|importantly|crucial...` |
| `weasel_some_say` | high | npov.weasel_words | `(?i)\b(some|many|most|critics|supporters|experts|scholars|observers|commentat...` |
| `weasel_it_is_said` | high | npov.weasel_words | `(?i)\b(it (is|was) (said|believed|claimed|reported|alleged|considered|thought...` |
| `peacock_renowned` | high | promo.peacock_terms | `(?i)\b(renowned|legendary|world[- ]class|world[- ]famous|iconic|trailblazing|...` |
| `promo_award_winning` | high | promo.promotional_phrasing | `(?i)\b(award[- ]winning|critically acclaimed|highly acclaimed|widely acclaime...` |
| `loaded_label_regime` | medium | npov.loaded_label | `(?i)\b(regime|dictatorship|junta|cabal|clique)\b` |
| `loaded_label_terrorist` | medium | npov.loaded_label | `(?i)\b(terrorist|terror group|jihadist|extremist|radical|militant|insurgent|r...` |
| `loaded_label_cult` | medium | npov.loaded_label | `(?i)\b(cult|sect|fringe|conspiracy theorist|denialist|denier|truther)\b` |
| `synth_therefore` | high | or.synth_marker | `(?i)(?:^|\.\s+)(therefore|thus|consequently|as a result|hence|this (proves|sh...` |
| `synth_combination_however` | high | or.synth_marker | `(?i)\bhowever,?\s+(this|these|that|those|the (above|preceding|foregoing))\s+(...` |
| `citation_needed_marker` | low | v.citation_needed_present | `\{\{(citation needed|cn|fact|cite)\}\}` |
| `dead_link_marker` | medium | v.dead_link_present | `\{\{(dead link|404)\}\}` |
| `self_published_blog` | high | rs.self_published_source | `(?i)\b(according to|as (stated|noted|written) on|via) (his|her|their|the [A-Z...` |
| `predatory_journal_marker` | medium | rs.predatory_publisher_to_verify | `(?i)\b(omics|frontiers in [a-z]+|hindawi|sciencepg|scirp|world scientific new...` |
| `press_release_as_source` | medium | rs.press_release_as_source | `(?i)\b(press release|company announcement|corporate communications|company sp...` |
| `promo_we_us_our` | medium | promo.first_person_voice | `(?i)(?:^|\.\s+)(we|us|our|i|me|my)\b` |
| `buzz_words_revolutionary` | high | promo.peacock_terms | `(?i)\b(revolutionary|groundbreaking|game[- ]changing|disruptive|next[- ]gener...` |
| `vague_attribution_studies_show` | high | v.vague_attribution_no_citation | `(?i)\b(studies? (show|have shown|suggest|indicate|find)|research (shows?|indi...` |
| `long_quote_block_marker` | medium | or.long_primary_quote | `(?:^|\n)>{1,3}\s+\S.{200,}` |
| `wp_blp_contentious_unsourced` | high | blp.contentious_claim_check_sourcing | `(?i)\b(allegedly|reportedly|accused of|charged with|convicted of|sued for|inv...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-wikipedia-quality-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-wikipedia-quality-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-wikipedia-quality-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-wikipedia-quality-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-wikipedia-quality-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-wikipedia-quality-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-wikipedia-quality-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-wikipedia-quality-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-wikipedia-quality-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_10` | high | grep-wikipedia-quality-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-wikipedia-quality-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-wikipedia-quality-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-wikipedia-quality-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-wikipedia-quality-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-wikipedia-quality-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-wikipedia-quality-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-wikipedia-quality-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-wikipedia-quality-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-wikipedia-quality-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-wikipedia-quality-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-wikipedia-quality-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-wikipedia-quality-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-wikipedia-quality-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-wikipedia-quality-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-wikipedia-quality-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_26` | high | grep-wikipedia-quality-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-wikipedia-quality-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-wikipedia-quality-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-wikipedia-quality-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-wikipedia-quality-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-wikipedia-quality-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-wikipedia-quality-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-wikipedia-quality-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)....` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-wikipedia-quality-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,160...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-wikipedia-quality-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-wikipedia-quality-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-wikipedia-quality-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-wikipedia-quality-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags).{0,...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-wikipedia-quality-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-wikipedia-quality-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}wikipedia.{0,24}quality.{0,24}flags)...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-wikipedia-quality-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-wikipedia-quality-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-wikipedia-quality-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-wikipedia-quality-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-wikipedia-quality-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-wikipedia-quality-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-wikipedia-quality-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

