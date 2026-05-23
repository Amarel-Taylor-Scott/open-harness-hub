# Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)

*rule-pack* · `rule-pack/grep-trade-compliance-flags` · v0.1.0 · beta

GREP detectors for export-control red flags: dual-use technology
to embargoed destinations, missing end-user diligence, ITAR
technical data outside licensed scope, deemed-export
signals, customer requesting EAR99 mis-classification.

| axis | value |
|---|---|
| industry | trade, trade.eccn, trade.itar, trade.sanctions, compliance |
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
| `embargoed_destination` | critical | trade.embargoed_destination | `(?i)\b(cuba|iran|north korea|dprk|syria|crimea|donetsk|luhansk|sudan|south su...` |
| `entity_list_hit` | critical | trade.entity_list | `(?i)(?:bis\s+)?entity\s+list\s+(?:hit|match|listed)|denied\s+persons\s+list|u...` |
| `ofac_sdn_hit` | critical | trade.ofac_sdn | `(?i)ofac\s+(?:sdn|sectoral|consolidated)\s+(?:hit|match|listed)|specially\s+d...` |
| `itar_technical_data` | critical | trade.itar.technical_data | `(?i)itar\s+(?:controlled\s+)?technical\s+data(?!.{0,200}(?:tata|technical\s+a...` |
| `deemed_export_signal` | high | trade.deemed_export | `(?i)(?:foreign\s+national|non[- ]?us\s+person|h1b|opt|j1)\s+(?:has\s+access\s...` |
| `ear99_self_certification` | medium | trade.ear99_unverified | `(?i)customer\s+states\s+(?:item\s+is\s+)?ear99|self[- ]?certif(?:y|ied|icatio...` |
| `red_flag_indicators` | high | trade.bis_red_flag_indicator | `(?i)(?:customer\s+(?:declines|refuses)\s+(?:to\s+identify|end[- ]?use|end[- ]...` |
| `diversion_signal` | critical | trade.diversion | `(?i)(?:onward\s+shipment\s+to|re[- ]?export\s+to|destined\s+for|ultimate\s+de...` |
| `encryption_classification_missing` | medium | trade.encryption_unclassified | `(?i)encryption\s+(?:functionality|module|library)(?!.{0,200}(?:cclasif|eccn\s...` |
| `dual_use_to_military_end_user` | critical | trade.dual_use_meu | `(?i)dual[- ]?use\s+(?:item|technology)\s+(?:to|for)\s+(?:military\s+end\s+use...` |
| `missing_end_user_certification` | high | trade.no_end_user_cert | `(?i)(?:no|absent|n[\.\/]?a)\s+(?:end[- ]?user|end[- ]?use)\s+(?:certification...` |
| `human_rights_concern` | high | trade.human_rights_screening | `(?i)(?:surveillance|biometric|facial[- ]?recognition|spyware|exploit\s+market...` |

