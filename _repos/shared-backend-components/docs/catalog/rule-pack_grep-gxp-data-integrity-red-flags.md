# GxP data-integrity red-flag detectors (21-CFR-11 / ALCOA+)

*rule-pack* · `rule-pack/grep-gxp-data-integrity-red-flags` · v0.1.0 · beta

GREP detectors for the highest-leverage 21-CFR-11 + ALCOA+ data-
integrity violations: missing audit trails, shared accounts, post-
hoc record alteration, validation gaps, missing electronic-
signature meaning, missing reason-for-change, manual data
transcription without verification. Pair with
`pipeline/gxp-validation-review`.

| axis | value |
|---|---|
| industry | pharma, pharma.gxp, compliance |
| capability | safety_gating, classification, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `audit_trail_disabled` | critical | gxp.audit_trail.disabled | `(?i)audit[- ]?trail\s+(?:disabled|turned\s+off|switched\s+off|not\s+(?:enable...` |
| `shared_account` | critical | gxp.shared_account | `(?i)(?:(?<!no\s)(?<!none\s)(?<!zero\s)(shared|generic|group|admin)\s+(?:accou...` |
| `post_hoc_alteration` | critical | gxp.post_hoc_alteration | `(?i)(modify|update|alter|edit|correct).*(?:past|prior|previous|already[- ]?(?...` |
| `validation_missing` | high | gxp.validation.missing | `(?i)(not[- ]?validated|validation\s+(?:not\s+(?:performed|complete)|pending|o...` |
| `missing_reason_for_change` | high | gxp.reason_for_change.missing | `(?i)(change|modification|edit|amendment)\s+without\s+(?:reason|justification|...` |
| `missing_signature_meaning` | high | gxp.signature.no_meaning | `(?i)e[- ]?signature.{0,80}without\s+(?:meaning|purpose|review|approval|author...` |
| `single_factor_signature` | high | gxp.signature.single_factor | `(?i)e[- ]?signature\s+via\s+password\s+only|single[- ]?factor\s+signature|pas...` |
| `manual_transcription_unverified` | medium | gxp.manual_transcription.unverified | `(?i)(manual|hand)\s+(?:transcription|entry|re[- ]?keying)\s+(?:from|of)\s+(?:...` |
| `backup_treated_as_archive` | medium | gxp.backup_not_archive | `(?i)backup\s+(?:is|serves\s+as|acts\s+as|replaces)\s+archive|no\s+separate\s+...` |
| `dynamic_record_static_export` | high | gxp.dynamic_record_flattened | `(?i)dynamic\s+record\s+(?:exported|archived)\s+as\s+(?:pdf|static|image)(?!.{...` |
| `test_data_in_production` | medium | gxp.test_data_in_prod | `(?i)test\s+data\s+in\s+(?:production|live|prod)|prod.*populated\s+with\s+test` |
| `unrestricted_blank_template` | medium | gxp.uncontrolled_template | `(?i)blank\s+(?:record|template|form)\s+(?:not\s+(?:numbered|controlled)|freel...` |
| `missing_audit_trail_review` | high | gxp.audit_trail.unreviewed | `(?i)audit[- ]?trail\s+(?:not\s+reviewed|review\s+(?:not\s+performed|skipped|d...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-gxp-data-integrity-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red.{0...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}r...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-gxp-data-integrity-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-gxp-data-integrity-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,2...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-gxp-data-integrity-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red.{0...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-gxp-data-integrity-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}r...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-gxp-data-integrity-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,2...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-gxp-data-integrity-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red.{0...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-gxp-data-integrity-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}r...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-gxp-data-integrity-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,2...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-gxp-data-integrity-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-gxp-data-integrity-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red.{0...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}r...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-gxp-data-integrity-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-gxp-data-integrity-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,2...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red.{0...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-gxp-data-integrity-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-gxp-data-integrity-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}r...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}re...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24}red...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-gxp-data-integrity-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,2...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-gxp-data-integrity-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}gxp.{0,24}data.{0,24}integrity.{0,24...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-gxp-data-integrity-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-gxp-data-integrity-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-gxp-data-integrity-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

