# RCRA hazardous waste + e-Manifest + DOT HMR flags

*rule-pack* · `rule-pack/grep-rcra-waste-flags` · v0.1.0 · beta

Detectors for 40 CFR 260-279 + e-Manifest + DOT 49 CFR 172 compliance gaps.

| axis | value |
|---|---|
| industry | waste, waste.rcra_tsdf, waste.generator, waste.universal |
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
| `generator_status_miscategorized_lqg` | critical | waste.generator.miscategorized | `(?i)(?:self[- ]?identified|categorized)\s+as\s+(?:a\s+)?(?:small\s+quantity\s...` |
| `accumulation_past_limit` | critical | waste.accumulation.exceeded | `(?i)(?:drums?|containers?)[\s\S]{0,200}?(?:over\s+1[0-9]{2}\s+days?\s+old|pas...` |
| `container_marking_missing` | high | waste.container.marking_missing | `(?i)(?:no\s+accumulation\s+start\s+date|drums?\s+(?:with|observed)\s+(?:with\...` |
| `secondary_containment_missing` | critical | waste.tank.no_secondary | `(?i)(?:tank[\s\S]{0,80}?(?:sat|located|positioned)[\s\S]{0,80}?(?:bare\s+asph...` |
| `incompatible_wastes_co_stored` | critical | waste.storage.incompatible | `(?i)(?:acid[\s\S]{0,80}?(?:cyanide|plating\s+sludge)|cyanide[\s\S]{0,80}?acid...` |
| `weekly_inspection_gap` | medium | waste.inspection.gap | `(?i)(?:weekly\s+(?:container\s+|tank\s+)?inspection|inspection\s+log)[\s\S]{0...` |
| `ldr_notification_missing` | critical | waste.ldr.missing | `(?i)(?:ldr|land\s+disposal\s+restriction)\s+notification\s+(?:missing|absent|...` |
| `dot_hazmat_training_missing` | high | waste.dot.no_training | `(?i)(?:signing\s+employee|shipping\s+signatory)\s+(?:held\s+)?(?:no\s+(?:curr...` |
| `contingency_plan_not_shared_lepc` | medium | waste.contingency.no_lepc | `(?i)(?:contingency\s+plan|emergency\s+plan)[\s\S]{0,200}?(?:never\s+(?:been\s...` |
| `satellite_accumulation_exceed_55gal` | medium | waste.satellite.exceeded | `(?i)satellite\s+accumulation[\s\S]{0,200}?(?:over\s+55\s+gal|exceed(?:ing|s|e...` |
| `biennial_report_missing` | medium | waste.biennial.missing | `(?i)(?:biennial\s+report|form\s+8700[- ]?13)\s+(?:missing|not\s+(?:filed|subm...` |
| `permit_expired_or_interim_no_part_b` | critical | waste.permit.expired | `(?i)(?:part\s+b\s+permit|tsdf\s+permit)\s+(?:expired|in\s+interim\s+status\s+...` |

