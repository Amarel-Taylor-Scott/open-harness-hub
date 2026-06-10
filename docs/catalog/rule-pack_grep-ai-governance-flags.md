# AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

*rule-pack* · `rule-pack/grep-ai-governance-flags` · v0.1.0 · beta

Detectors for AI governance + conformity assessment gaps.

| axis | value |
|---|---|
| industry | ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001, privacy |
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
| `annex_iii_no_ce_marking` | critical | ai_gov.eu_act.no_ce | `(?i)(?:annex\s+iii|high[- ]?risk)[\s\S]{0,200}?(?:no\s+(?:notified[- ]?body|c...` |
| `annex_iv_doc_missing` | high | ai_gov.eu_act.annex_iv_missing | `(?i)annex\s+iv\s+technical\s+(?:file|documentation)\s+(?:consists\s+of\s+a\s+...` |
| `data_governance_art10_missing` | high | ai_gov.eu_act.art10_missing | `(?i)(?:no\s+art(?:icle)?\s*10\s+data\s+governance|art(?:icle)?\s*10\s+(?:bias...` |
| `no_human_oversight_art14` | critical | ai_gov.eu_act.art14_missing | `(?i)(?:art(?:icle)?\s*14|human\s+oversight)\s+(?:not\s+(?:implemented|specifi...` |
| `logs_under_6_months_art12` | high | ai_gov.eu_act.art12_logs | `(?i)(?:logs?|system\s+logs?)\s+(?:retained|rotated|kept)\s+(?:every\s+)?(?:[1...` |
| `art22_no_human_review_path` | critical | ai_gov.gdpr.art22_violation | `(?i)(?:automated\s+decision|art(?:icle)?\s*22)[\s\S]{0,200}?(?:no\s+human\s+r...` |
| `gpai_no_art53_transparency` | critical | ai_gov.gpai.no_art53 | `(?i)(?:gpai|general[- ]?purpose\s+ai|foundation\s+model)[\s\S]{0,200}?(?:no\s...` |
| `serious_incident_not_reported_15d` | critical | ai_gov.incident.unreported | `(?i)(?:serious\s+incident|wave\s+of\s+discriminatory|adverse\s+outcome)[\s\S]...` |
| `aims_iso42001_unsigned` | medium | ai_gov.iso42001.unsigned | `(?i)(?:iso\s*(?:[/]?iec)?\s*42001|aims)\s+(?:ai\s+)?policy\s+(?:remains\s+an\...` |
| `prohibited_practice` | critical | ai_gov.prohibited | `(?i)(?:social\s+scoring|untargeted\s+(?:scraping|facial\s+recognition\s+(?:da...` |
| `no_model_card` | medium | ai_gov.model_card.missing | `(?i)(?:no\s+model\s+card|model\s+card\s+(?:missing|absent|not\s+published|not...` |
| `fria_missing_public_sector` | high | ai_gov.fria.missing | `(?i)(?:fria|fundamental\s+rights\s+impact\s+assessment)\s+(?:missing|not\s+(?...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-ai-governance-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-ai-governance-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-ai-governance-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-ai-governance-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-ai-governance-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-ai-governance-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-ai-governance-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-ai-governance-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-ai-governance-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-ai-governance-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-ai-governance-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-ai-governance-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-ai-governance-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-ai-governance-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-ai-governance-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-ai-governance-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-ai-governance-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-ai-governance-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-ai-governance-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-ai-governance-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-ai-governance-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-ai-governance-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-ai-governance-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-ai-governance-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-ai-governance-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-ai-governance-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-ai-governance-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-ai-governance-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-ai-governance-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-ai-governance-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-ai-governance-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-ai-governance-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-ai-governance-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,1...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-ai-governance-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-ai-governance-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-ai-governance-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,16...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-ai-governance-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-ai-governance-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,160}...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-ai-governance-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-ai-governance-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}ai.{0,24}governance.{0,24}flags).{0,...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-ai-governance-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-ai-governance-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-ai-governance-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-ai-governance-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-ai-governance-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-ai-governance-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-ai-governance-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-ai-governance-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-ai-governance-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-ai-governance-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

