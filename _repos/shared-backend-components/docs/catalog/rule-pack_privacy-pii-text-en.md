# Privacy PII (English text)

*rule-pack* · `rule-pack/privacy-pii-text-en` · v0.1.0 · stable

Baseline GREP rule pack for detecting common PII in English text.
Emails, phone numbers, US SSN, passport numbers, IBANs, IPv4. Designed
to feed `harness/redact-pii-text` and any downstream pipeline that
needs a hard PII gate before model or external calls.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `email` | high | pii.contact | `(?i)[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` |
| `phone_e164` | medium | pii.contact | `\+?[1-9]\d{1,14}` |
| `us_ssn` | critical | pii.id | `\b\d{3}-\d{2}-\d{4}\b` |
| `passport_generic` | critical | pii.id | `(?i)passport (?:no\.?|number)?\s*:?\s*[A-Z0-9]{6,9}` |
| `iban` | high | pii.financial | `[A-Z]{2}\d{2}[A-Z0-9]{4,30}` |
| `ipv4` | low | pii.network | `\b(?:\d{1,3}\.){3}\d{1,3}\b` |
| `scale_expansion_v1_critical_signal_01` | high | privacy-pii-text-en.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_02` | medium | privacy-pii-text-en.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_03` | medium | privacy-pii-text-en.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_04` | medium | privacy-pii-text-en.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_05` | high | privacy-pii-text-en.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_06` | high | privacy-pii-text-en.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | privacy-pii-text-en.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}...` |
| `scale_expansion_v1_missing_evidence_08` | medium | privacy-pii-text-en.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(...` |
| `scale_expansion_v1_critical_signal_09` | medium | privacy-pii-text-en.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_10` | high | privacy-pii-text-en.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_11` | high | privacy-pii-text-en.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_12` | medium | privacy-pii-text-en.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | privacy-pii-text-en.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_14` | medium | privacy-pii-text-en.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_15` | high | privacy-pii-text-en.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}...` |
| `scale_expansion_v1_missing_evidence_16` | high | privacy-pii-text-en.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(...` |
| `scale_expansion_v1_critical_signal_17` | medium | privacy-pii-text-en.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_18` | medium | privacy-pii-text-en.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_19` | medium | privacy-pii-text-en.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_20` | high | privacy-pii-text-en.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_21` | high | privacy-pii-text-en.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_22` | medium | privacy-pii-text-en.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | privacy-pii-text-en.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}...` |
| `scale_expansion_v1_missing_evidence_24` | medium | privacy-pii-text-en.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(...` |
| `scale_expansion_v1_critical_signal_25` | high | privacy-pii-text-en.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_26` | high | privacy-pii-text-en.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_27` | medium | privacy-pii-text-en.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_28` | medium | privacy-pii-text-en.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | privacy-pii-text-en.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_30` | high | privacy-pii-text-en.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_31` | high | privacy-pii-text-en.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}...` |
| `scale_expansion_v1_missing_evidence_32` | medium | privacy-pii-text-en.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(...` |
| `scale_expansion_v1_critical_signal_33` | medium | privacy-pii-text-en.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?...` |
| `scale_expansion_v1_owner_gap_34` | medium | privacy-pii-text-en.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:evide...` |
| `scale_expansion_v1_deadline_risk_35` | high | privacy-pii-text-en.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_redaction_risk_36` | high | privacy-pii-text-en.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | privacy-pii-text-en.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:e...` |
| `scale_expansion_v1_citation_gap_38` | medium | privacy-pii-text-en.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(?:ev...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | privacy-pii-text-en.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}...` |
| `scale_expansion_v1_missing_evidence_40` | high | privacy-pii-text-en.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|privacy.{0,24}pii.{0,24}text.{0,24}en).{0,160}(...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | privacy-pii-text-en.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | privacy-pii-text-en.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | privacy-pii-text-en.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | privacy-pii-text-en.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | privacy-pii-text-en.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | privacy-pii-text-en.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | privacy-pii-text-en.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | privacy-pii-text-en.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | privacy-pii-text-en.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | privacy-pii-text-en.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

