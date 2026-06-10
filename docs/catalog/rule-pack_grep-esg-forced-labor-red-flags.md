# ESG / forced-labor red-flag detectors (the 'S' of ESG)

*rule-pack* · `rule-pack/grep-esg-forced-labor-red-flags` · v0.2.0 · beta

Heuristic regex detectors for the 11 ILO forced-labor indicators
+ child labor + recruitment-fee abuse + tier-3/4 supply-chain
transparency gaps + 12 high-risk corridors. Designed to be run
over: supplier policy texts, supplier self-assessments, worker
grievance transcripts (post-PII redaction), audit reports,
contract clauses.

Multi-lingual core covering the major garment / electronics /
agriculture / construction labor corridors:
 - English (lead-company HQ language)
 - 简体中文 (China factories, Xinjiang corridor)
 - हिन्दी (India, Bangladesh garment, Sialkot sports goods)
 - বাংলা (Bangladesh garment, brick kilns)
 - 한국어 (Korean supplier paperwork)
 - tiếng Việt (Vietnam garment + electronics)
 - ภาษาไทย (Thailand seafood + electronics, Mae Sot corridor)
 - bahasa Indonesia (palm oil + electronics)
 - Filipino / Tagalog (BPO + electronics)
 - español (Latin America agriculture, maquilas)
 - português (Brazil agriculture, beef supply chain)
 - français (West Africa cocoa)
 - العربية (Gulf states kafala system)

Pair with `pipeline/supplier-policy-grading` (with the env + gov
packs) for full ESG coverage. These are FAST FIRST-PASS heuristics
that TRIGGER reviews — not authoritative determinations.

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
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
| `passport_retention` | critical | ilo.retention_of_identity_documents | `(?i)\b(passport|id|identity document|document|身份证|护照|पासपोर्ट|পাসপোর্ট|여권|hộ ...` |
| `passport_retention_arabic_kafala` | critical | ilo.retention_of_identity_documents.kafala | `(?:احتجاز جواز|سحب جواز|kafala|sponsorship system|tied to (?:sponsor|employer...` |
| `recruitment_fee_abuse` | high | ilo.debt_bondage | `(?i)(recruitment|placement|broker|agency|agent)[- ]?fee|deposit (?:before|pri...` |
| `wage_withholding` | high | ilo.withholding_of_wages | `(?i)wage(s)?\s+(?:held|withheld|not paid|delayed|deduct|garnish|advance.*reco...` |
| `restricted_movement_dormitory` | critical | ilo.restriction_of_movement | `(?i)(dormitory|hostel|compound|barrack)\b.{0,30}?(?:locked|guarded|fenced|res...` |
| `excessive_overtime` | medium | ilo.excessive_overtime | `(?i)(\d{1,3}|seventy|eighty|ninety|hundred)\s*(?:\+|plus)?\s*hour(s)?\s+(?:pe...` |
| `deceptive_recruitment` | high | ilo.deception | `(?i)(promised|told)\s+(?:job|salary|wage|role).*(?:different|other|not what)|...` |
| `child_labor` | critical | ilo.child_labor | `(?i)\b(child|minor|under(-| )?age|under 1[5678]|under 16|under 18|14[- ]year[...` |
| `threats_intimidation` | critical | ilo.intimidation_and_threats | `(?i)(threat|intimidat|coerc|punish|beat|hit|slap|abus).*(worker|labourer|labo...` |
| `isolation_unfree_communication` | high | ilo.isolation | `(?i)(?:no|forbidden|cannot|may not use|not allowed to use|prohibited from usi...` |
| `abusive_living_conditions` | high | ilo.abusive_working_and_living_conditions | `(?i)(unsanitary|unsafe|unventilated|no (?:water|toilet|food|heating|cooling)|...` |
| `audit_gap_tier_3_4` | medium | supply_chain.audit_gap_tier_3_4 | `(?i)(unable to|cannot|could not)\s+(?:trace|verify|audit|confirm)\s+(?:them|t...` |
| `sourcing_high_risk_corridor` | high | supply_chain.high_risk_corridor | `(?i)\b(xinjiang|XUAR|新疆|uyghur|qaem shahr|sialkot|raipur|bhainsa|firozabad|ma...` |
| `uyghur_forced_labor_specific` | critical | supply_chain.uyghur_forced_labor | `(?i)(xpcc|xinjiang production and construction|aksu|hotan|kashgar|labor trans...` |
| `cocoa_west_africa_child_labor` | critical | supply_chain.cocoa_child_labor | `(?i)(cote d.ivoire|côte d.ivoire|ivory coast|ghana cocoa).*(?:child|minor|und...` |
| `seafood_thai_forced_labor` | critical | supply_chain.thai_seafood | `(?i)(thai|thailand|samut sakhon|ranong).*(?:fishing|vessel|boat|trawler|peeli...` |
| `abusive_overtime_consent` | high | ilo.excessive_overtime.consent | `(?i)(must|required to work|forced to work|compulsory)\s+(?:overtime|extra hou...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-esg-forced-labor-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}re...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-esg-forced-labor-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{0,2...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-esg-forced-labor-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-esg-forced-labor-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-esg-forced-labor-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_citation_gap_06` | high | grep-esg-forced-labor-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-esg-forced-labor-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-esg-forced-labor-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}r...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-esg-forced-labor-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}re...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-esg-forced-labor-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{0,2...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-esg-forced-labor-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-esg-forced-labor-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-esg-forced-labor-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-esg-forced-labor-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-esg-forced-labor-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-esg-forced-labor-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}r...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-esg-forced-labor-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}re...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-esg-forced-labor-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{0,2...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-esg-forced-labor-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-esg-forced-labor-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-esg-forced-labor-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-esg-forced-labor-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-esg-forced-labor-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-esg-forced-labor-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}r...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-esg-forced-labor-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}re...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-esg-forced-labor-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{0,2...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-esg-forced-labor-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-esg-forced-labor-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-esg-forced-labor-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_citation_gap_30` | high | grep-esg-forced-labor-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-esg-forced-labor-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-esg-forced-labor-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}r...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-esg-forced-labor-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}re...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-esg-forced-labor-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{0,2...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-esg-forced-labor-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-esg-forced-labor-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-esg-forced-labor-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red....` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-esg-forced-labor-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}red.{...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-esg-forced-labor-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-esg-forced-labor-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}esg.{0,24}forced.{0,24}labor.{0,24}r...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-esg-forced-labor-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-esg-forced-labor-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-esg-forced-labor-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

