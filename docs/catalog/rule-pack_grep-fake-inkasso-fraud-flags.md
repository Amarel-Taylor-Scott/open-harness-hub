# Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)

*rule-pack* · `rule-pack/grep-fake-inkasso-fraud-flags` · v0.1.0 · beta

GREP detectors for the 10 Verbraucherzentrale Fake-Inkasso
indicators. Used by `pipeline/bill-info-extract-fraud-detect-recommend`
as a deterministic FIRST PASS before the LLM-based fraud-detect
call — fires hard-rule indicators that the LLM call then weights
+ classifies.

Sourced from Sviatoslav Grabovsky's Bill_info AI (Bill_info AI on
Hugging Face Spaces) which uses these indicators across both the
Gemma 4 26B fraud-detect call AND a deterministic business_rules
layer.

| axis | value |
|---|---|
| industry | bureaucracy_translation, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee |
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
| `foreign_iban_non_dach` | critical | fake_inkasso.iban.foreign_non_dach | `(?i)\b(?:IBAN[:\s]*)?(?:PL|CZ|SK|LV|LT|EE|HU|RO|BG|HR|SI|GR|MT|CY|TR|UA|RU|BY...` |
| `private_person_recipient` | critical | fake_inkasso.recipient.private_person | `(?i)(?:empfänger|recipient|payee|payment\s+to)[:\s]+(?:herr|frau|mr|mrs|ms)\s...` |
| `legal_threats_first_letter` | critical | fake_inkasso.legal_threats.no_prior_mahnung | `(?i)(?:gerichtsvollzieher|gerichtliche\s+schritte|zwangsvollstreckung|schufa[...` |
| `extreme_deadline_24_72h` | critical | fake_inkasso.deadline.extreme_24_72h | `(?i)(?:zahlungsfrist|frist|deadline|bis\s+spätestens)[:\s]+(?:24|48|72)\s*(?:...` |
| `missing_handelsregister` | medium | fake_inkasso.missing_handelsregister | `(?i)inkasso(?:firma|gmbh|ag|dienst)[\s\S]{0,500}?(?!.{0,400}(?:hrb\s*\d+|hra\...` |
| `unclear_creditor` | medium | fake_inkasso.unclear_creditor | `(?i)(?:gläubiger|creditor|original[- ]?creditor)[:\s]*(?:n[\.\/]?a|unbekannt|...` |
| `dubious_excess_fees` | medium | fake_inkasso.dubious_excess_fees | `(?i)(?:bearbeitungsgebühr|express[- ]?versand|express[- ]?versandkosten|sonde...` |
| `phantom_company_name` | medium | fake_inkasso.phantom_company_name | `(?i)(?:forderungsmanagement|inkassodienst|rechtsabteilung|forderungsstelle|ma...` |
| `premium_phone_number` | medium | fake_inkasso.premium_phone | `(?i)(?:tel(?:efon)?|phone|hotline)[:\s]+(?:0?900\s?\d+|0?180\s?\d+|\+49[- ]?9...` |
| `letzte_mahnung_first_letter` | medium | fake_inkasso.pressure_tactics | `(?i)\bletzte\s+mahnung\b|\bfinal\s+(?:reminder|notice)\b|\bsofortige\s+(?:zah...` |
| `missing_aufsichtsbehoerde` | low | fake_inkasso.missing_aufsichtsbehoerde | `(?i)inkasso[\s\S]{0,500}?(?!.{0,400}aufsichtsbehörde\s+(?:oberlandesgericht|o...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-fake-inkasso-fraud-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}flags)...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}f...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-fake-inkasso-fraud-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-fake-inkasso-fraud-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fla...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,2...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-fake-inkasso-fraud-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}flags)...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-fake-inkasso-fraud-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}f...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fla...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-fake-inkasso-fraud-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,2...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-fake-inkasso-fraud-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}flags)...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-fake-inkasso-fraud-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}f...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-fake-inkasso-fraud-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fla...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,2...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-fake-inkasso-fraud-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-fake-inkasso-fraud-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}flags)...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}f...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-fake-inkasso-fraud-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fla...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-fake-inkasso-fraud-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,2...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}flags)...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-fake-inkasso-fraud-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-fake-inkasso-fraud-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}f...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fl...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24}fla...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-fake-inkasso-fraud-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,2...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-fake-inkasso-fraud-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}fake.{0,24}inkasso.{0,24}fraud.{0,24...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-fake-inkasso-fraud-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-fake-inkasso-fraud-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-fake-inkasso-fraud-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

