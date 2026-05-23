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

