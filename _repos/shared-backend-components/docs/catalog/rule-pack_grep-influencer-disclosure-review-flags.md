# Influencer Disclosure Review grep flags

*rule-pack* · `rule-pack/grep-influencer-disclosure-review-flags` · v0.1.0 · experimental

Ten local triage detectors for influencer disclosure review packets.

| axis | value |
|---|---|
| industry | marketing_ops.claims, media.distribution |
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
| `sponsored_hidden` | critical | influencer_disclosure_review.sponsored_hidden | `(?i)sponsored.{0,36}hidden` |
| `affiliate_link` | critical | influencer_disclosure_review.affiliate_link | `(?i)affiliate.{0,36}link` |
| `material_connection` | high | influencer_disclosure_review.material_connection | `(?i)material.{0,36}connection` |
| `claim_unsupported` | high | influencer_disclosure_review.claim_unsupported | `(?i)claim.{0,36}unsupported` |
| `before_after` | high | influencer_disclosure_review.before_after | `(?i)before.{0,36}after` |
| `testimonial` | high | influencer_disclosure_review.testimonial | `(?i)testimonial` |
| `hashtag_absent` | medium | influencer_disclosure_review.hashtag_absent | `(?i)hashtag.{0,36}absent` |
| `brief_mismatch` | medium | influencer_disclosure_review.brief_mismatch | `(?i)brief.{0,36}mismatch` |
| `approval_missing` | medium | influencer_disclosure_review.approval_missing | `(?i)approval.{0,36}missing` |
| `platform_disclosure` | medium | influencer_disclosure_review.platform_disclosure | `(?i)platform.{0,36}disclosure` |
| `scale_expansion_v1_critical_signal_01` | high | grep-influencer-disclosure-review-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}influencer.{0,24}disclosure.{0,24}rev...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-influencer-disclosure-review-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review.{0...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-influencer-disclosure-review-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-influencer-disclosure-review-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revi...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-influencer-disclosure-review-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-influencer-disclosure-review-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-influencer-disclosure-review-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}influencer.{0,24}disclosure.{0,24}r...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-influencer-disclosure-review-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}influencer.{0,24}disclosure.{0,24}re...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-influencer-disclosure-review-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}influencer.{0,24}disclosure.{0,24}rev...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-influencer-disclosure-review-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review.{0...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-influencer-disclosure-review-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-influencer-disclosure-review-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revi...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-influencer-disclosure-review-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-influencer-disclosure-review-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-influencer-disclosure-review-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}influencer.{0,24}disclosure.{0,24}r...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-influencer-disclosure-review-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}influencer.{0,24}disclosure.{0,24}re...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-influencer-disclosure-review-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}influencer.{0,24}disclosure.{0,24}rev...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-influencer-disclosure-review-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review.{0...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-influencer-disclosure-review-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-influencer-disclosure-review-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revi...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-influencer-disclosure-review-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-influencer-disclosure-review-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-influencer-disclosure-review-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}influencer.{0,24}disclosure.{0,24}r...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-influencer-disclosure-review-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}influencer.{0,24}disclosure.{0,24}re...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-influencer-disclosure-review-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}influencer.{0,24}disclosure.{0,24}rev...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-influencer-disclosure-review-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review.{0...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-influencer-disclosure-review-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-influencer-disclosure-review-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revi...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-influencer-disclosure-review-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-influencer-disclosure-review-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-influencer-disclosure-review-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}influencer.{0,24}disclosure.{0,24}r...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-influencer-disclosure-review-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}influencer.{0,24}disclosure.{0,24}re...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-influencer-disclosure-review-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}influencer.{0,24}disclosure.{0,24}rev...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-influencer-disclosure-review-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review.{0...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-influencer-disclosure-review-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-influencer-disclosure-review-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}influencer.{0,24}disclosure.{0,24}revi...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-influencer-disclosure-review-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}revie...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-influencer-disclosure-review-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}influencer.{0,24}disclosure.{0,24}review...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-influencer-disclosure-review-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}influencer.{0,24}disclosure.{0,24}r...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-influencer-disclosure-review-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}influencer.{0,24}disclosure.{0,24}re...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-influencer-disclosure-review-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-influencer-disclosure-review-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-influencer-disclosure-review-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

