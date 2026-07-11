# Human-trafficking recruitment + solicitation flags (UGC triage)

*rule-pack* · `rule-pack/grep-human-trafficking-ugc-flags` · v0.1.0 · experimental

DEFENSIVE-USE rule pack for Trust + Safety triage of user-generated
content (job-listing platforms, classifieds, escort directories,
immigration forums, dating apps). Detects RECRUITMENT-stage signals
(the Polaris Project + ILO labor-trafficking indicator taxonomy) and
SOLICITATION-stage signals (commercial sex with control / coercion
markers, transit-corridor cues, debt-bondage references).

NOT a CSAM detector. CSAM-suspicion routes to
`rule-pack/grep-platform-moderation-flags` -> `csam_referral_route`
which triggers the NCMEC packet path WITHOUT model classification
(see `pattern/critical-tier-output-override`).

Patterns are coarse triage filters meant to escalate a post to a
trained T+S reviewer with the relevant indicator surfaced. They are
NOT determinations and SHOULD NOT auto-action. Co-occurrence of >=2
indicators is the conventional threshold for escalation; single hits
are review queue entries.

Sources: Polaris Project National Human Trafficking Hotline
indicator taxonomy; ILO Hard-to-See Hidden in Plain Sight forced
labour indicators (11-indicator framework); UNODC Global Report on
Trafficking in Persons (2022); FBI Innocence Lost National Initiative
public-facing typology.

| axis | value |
|---|---|
| industry | compliance, media, humanitarian, humanitarian.trafficking |
| capability | classification, safety_gating |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `labor_recruit_too_good_to_be_true` | high | ts.trafficking.labor.recruit.unrealistic_offer | `(?i)(?:no\s+experience\s+(?:needed|required|necessary)|earn\s+\$?\d{2,3}[k,]?...` |
| `labor_recruit_transport_lodging_bundled` | high | ts.trafficking.labor.recruit.bundled_control | `(?i)(?:transport(?:ation)?\s+(?:included|provided|covered)|housing\s+(?:inclu...` |
| `labor_recruit_passport_document_handling` | critical | ts.trafficking.labor.indicator.doc_retention | `(?i)(?:we['’]?ll\s+(?:hold|keep|secure)\s+(?:your\s+)?passport|surrender\s+(?...` |
| `labor_recruit_recruitment_fee` | high | ts.trafficking.labor.indicator.fee_bondage | `(?i)(?:recruitment\s+fee|placement\s+fee|broker\s+fee|agent\s+fee)\s*(?:of\s+...` |
| `labor_indicator_wage_withholding` | high | ts.trafficking.labor.indicator.wage_withholding | `(?i)(?:wages?|pay|salary)\s+(?:will\s+be\s+)?(?:held|withheld|in\s+escrow|pai...` |
| `labor_indicator_restricted_movement` | critical | ts.trafficking.labor.indicator.restricted_movement | `(?i)(?:not\s+allowed\s+to\s+leave|cannot\s+leave\s+(?:premises|site|compound|...` |
| `labor_indicator_isolation_language` | critical | ts.trafficking.labor.indicator.isolation | `(?i)(?:no\s+contact\s+with\s+(?:family|outside)|phone\s+(?:held|taken|confisc...` |
| `labor_corridor_high_risk_routing` | medium | ts.trafficking.labor.corridor.high_risk_route | `(?i)(?:travel|fly|cross)\s+(?:via|through|stop\s+in)\s+(?:dubai|doha|kuala\s+...` |
| `sex_traf_control_marker_third_party_manager` | high | ts.trafficking.sex.control.third_party | `(?i)(?:my\s+(?:manager|daddy|boss)\s+(?:answers|handles|takes)\s+(?:the\s+)?(...` |
| `sex_traf_control_marker_no_choice_language` | critical | ts.trafficking.sex.control.coerced_speech | `(?i)(?:i\s+(?:cannot|can'?t)\s+(?:refuse|say\s+no|choose)|i\s+have\s+to\s+(?:...` |
| `sex_traf_control_marker_debt_repayment` | critical | ts.trafficking.sex.control.debt_bondage | `(?i)(?:working\s+off\s+(?:my\s+)?debt|paying\s+(?:back\s+)?(?:my\s+)?(?:trave...` |
| `sex_traf_minor_age_dispute_signal` | critical | ts.trafficking.sex.minor.age_dispute | `(?i)(?:looks?\s+(?:young|underage|barely\s+legal)\s+but\s+(?:she|he|they)\s+(...` |
| `sex_traf_transit_circuit_pattern` | medium | ts.trafficking.sex.indicator.transit_circuit | `(?i)(?:in\s+(?:town|city)\s+(?:for\s+)?(?:tonight\s+only|24\s+hrs|48\s+hours|...` |
| `sex_traf_branding_tattoo_reference` | high | ts.trafficking.sex.indicator.branding | `(?i)(?:property\s+of\s+\w+\s+tattoo|branded\s+(?:with|by)\s+(?:my\s+)?(?:dadd...` |
| `sex_traf_indoor_brothel_signals` | high | ts.trafficking.sex.indicator.indoor_venue | `(?i)(?:multiple\s+(?:girls|women)\s+(?:available|on[- ]site)\s+(?:at|in)\s+(?...` |
| `victim_voice_disclosure_help_seeking` | critical | ts.trafficking.victim.disclosure | `(?i)(?:i\s+(?:am|was)\s+being\s+(?:held|forced|kept|trafficked)|help\s+me\s+(...` |
| `victim_voice_third_party_writes_on_behalf` | high | ts.trafficking.victim.proxy_writer | `(?i)(?:i\s+(?:am|'?m)\s+writing\s+(?:for|on\s+behalf\s+of)\s+(?:her|him|them)...` |
| `hotline_or_referral_mention` | low | ts.trafficking.referral.hotline_reference | `(?i)(?:national\s+human\s+trafficking\s+hotline|1[- ]?888[- ]?373[- ]?7888|po...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-human-trafficking-ugc-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-human-trafficking-ugc-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-human-trafficking-ugc-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-human-trafficking-ugc-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,2...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-human-trafficking-ugc-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-human-trafficking-ugc-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-human-trafficking-ugc-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-human-trafficking-ugc-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-human-trafficking-ugc-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-human-trafficking-ugc-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-human-trafficking-ugc-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-human-trafficking-ugc-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,2...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-human-trafficking-ugc-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-human-trafficking-ugc-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-human-trafficking-ugc-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-human-trafficking-ugc-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-human-trafficking-ugc-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-human-trafficking-ugc-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-human-trafficking-ugc-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-human-trafficking-ugc-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,2...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-human-trafficking-ugc-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-human-trafficking-ugc-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-human-trafficking-ugc-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-human-trafficking-ugc-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-human-trafficking-ugc-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-human-trafficking-ugc-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-human-trafficking-ugc-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-human-trafficking-ugc-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,2...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-human-trafficking-ugc-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-human-trafficking-ugc-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-human-trafficking-ugc-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-human-trafficking-ugc-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-human-trafficking-ugc-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-human-trafficking-ugc-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}fla...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-human-trafficking-ugc-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-human-trafficking-ugc-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,2...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-human-trafficking-ugc-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-human-trafficking-ugc-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0,24}...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-human-trafficking-ugc-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-human-trafficking-ugc-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}human.{0,24}trafficking.{0,24}ugc.{0...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-human-trafficking-ugc-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-human-trafficking-ugc-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-human-trafficking-ugc-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

