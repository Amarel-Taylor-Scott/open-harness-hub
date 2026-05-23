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

