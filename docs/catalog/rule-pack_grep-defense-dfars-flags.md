# Defense DFARS + CMMC + counterfeit-parts red-flag detectors

*rule-pack* · `rule-pack/grep-defense-dfars-flags` · v0.1.0 · beta

GREP detectors for DFARS / CMMC / SAE AS5553 / Section 889 / SAM exclusion.

| axis | value |
|---|---|
| industry | defense, defense.dfars, defense.counterfeit_parts, defense.cmmc |
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
| `no_cmmc_level_assigned` | critical | defense.cmmc.no_level | `(?i)cmmc\s+(?:level\s+)?(?:not\s+(?:assigned|determined|specified)|tbd|n[\.\/...` |
| `dfars_7012_breach_unreported` | critical | defense.cyber.dfars_7012_breach | `(?i)(?:cyber\s+(?:incident|breach))\s+(?:not\s+reported|past\s+72\s+hours)|di...` |
| `section_889_telecom` | critical | defense.sec_889.covered_telecom | `(?i)(?:huawei|zte|hytera|hikvision|dahua)\s+(?:equipment|gear|hardware|compon...` |
| `counterfeit_part_indicator` | critical | defense.counterfeit_parts.indicator | `(?i)(?:counterfeit|suspect[- ]?counterfeit|unmarked|unauthorized\s+distributo...` |
| `sam_exclusion_hit` | critical | defense.sam.exclusion | `(?i)sam(?:\.gov)?\s+(?:exclusion|debarred|suspended)\s+(?:list|hit)|excluded\...` |
| `itar_unlicensed_transfer` | critical | defense.itar.unlicensed | `(?i)itar\s+(?:controlled\s+)?(?:technical\s+data|defense\s+article)\s+(?:tran...` |
| `buy_american_noncompliance` | high | defense.buy_american | `(?i)buy\s+american\s+(?:noncompliance|violation|exception\s+not\s+claimed)|fo...` |
| `nist_800_171_gap` | high | defense.nist_800_171.gap | `(?i)nist\s+800[- ]?171\s+(?:control|requirement)\s+(?:gap|missing|not\s+imple...` |
| `supply_chain_no_traceability` | high | defense.supply_chain.no_traceability | `(?i)supply[- ]?chain\s+(?:traceability|provenance)\s+(?:not\s+(?:established|...` |
| `cui_marking_missing` | medium | defense.cui.marking_missing | `(?i)controlled\s+unclassified\s+information|\bcui\b(?!.{0,200}(?:properly\s+m...` |
| `as5553_no_inspection` | high | defense.counterfeit_parts.no_as5553 | `(?i)(?:as5553|as6081|sae\s+aerospace\s+standard)\s+(?:not\s+followed|gap)|ele...` |

