# Customs entry / FTA / forced-labor flags (US CBP)

*rule-pack* · `rule-pack/grep-customs-broker-flags` · v0.1.0 · beta

Detectors for customs-entry compliance gaps.

| axis | value |
|---|---|
| industry | customs, customs.entry, customs.tariff, customs.fta, trade |
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
| `isf_late_filing` | critical | customs.isf.late_filing | `(?i)(?:isf|importer\s+security\s+filing|10\+2)\s+(?:late|past\s+24\s*h|filed\...` |
| `forced_labor_wro_match` | critical | customs.forced_labor.wro | `(?i)(?:wro|withhold\s+release\s+order|forced[- ]?labor\s+section\s+307|19\s+u...` |
| `uflpa_entity_match` | critical | customs.uflpa.entity_match | `(?i)uflpa\s+(?:entity\s+list|presumption)\s+(?:match|hit|target)|xinjiang\s+p...` |
| `add_cvd_evasion_risk` | critical | customs.add_cvd.evasion | `(?i)(?:add\b|antidumping)|cvd\s+(?:evasion|circumvention|transshipment)\s+(?:...` |
| `fta_no_origin_cert` | high | customs.fta.no_origin_cert | `(?i)(?:usmca|korus|cptpp|nafta)\s+(?:claim|preference)(?!.{0,300}(?:certifica...` |
| `hts_misclassification` | high | customs.hts.misclassification | `(?i)hts(?:us)?\s+(?:classification\s+)?(?:wrong|incorrect|protest|reconciliat...` |
| `country_of_origin_marking_missing` | medium | customs.coo.marking_missing | `(?i)country[- ]?of[- ]?origin\s+(?:marking)?\s+(?:missing|absent|not\s+conspi...` |
| `valuation_undervalue` | high | customs.valuation.undervalue | `(?i)(?:transaction\s+value|valuation)\s+(?:significantly\s+below|under)\s+(?:...` |
| `ip_rights_counterfeit` | critical | customs.ip_rights.counterfeit | `(?i)(?:counterfeit|trademark\s+infringement|piratical)\s+(?:goods|merchandise...` |
| `ctpat_decertification_risk` | high | customs.ctpat.decertification | `(?i)c[- ]?tpat\s+(?:decertif|suspension|tier\s+(?:1|two)\s+rated|noncompliance)` |
| `reasonable_care_documentation_gap` | medium | customs.reasonable_care.gap | `(?i)reasonable\s+care\s+(?:documentation\s+)?(?:gap|missing|not\s+(?:document...` |
| `binding_ruling_request_needed` | low | customs.ruling.no_binding | `(?i)(?:binding\s+ruling|ruling\s+letter)\s+(?:not\s+(?:requested|obtained)|ne...` |

