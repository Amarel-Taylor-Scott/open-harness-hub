# Real estate DD red-flag detectors

*rule-pack* · `rule-pack/grep-real-estate-dd-red-flags` · v0.1.0 · beta

GREP detectors for title/ESA/structural/zoning issues.

| axis | value |
|---|---|
| industry | real_estate, real_estate.due_diligence |
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
| `open_permit` | critical | real_estate.title.open_permit | `(?i)(?:open|expired|unresolved)\s+(?:building\s+)?permit` |
| `unrecorded_transfer` | critical | real_estate.title.unrecorded | `(?i)unrecorded\s+(?:transfer|deed|conveyance|mortgage)` |
| `mechanics_lien` | high | real_estate.title.mechanics_lien | `(?i)mechanic[''']?s?\s+lien|materialmen[''']?s\s+lien|construction\s+lien` |
| `environmental_rec` | critical | real_estate.environmental.rec | `(?i)(?<!no\s)(?<!no\sknown\s)(?<!no\sidentified\s)\b(?:recognized\s+environme...` |
| `vapor_intrusion` | high | real_estate.environmental.vapor_intrusion | `(?i)vapor\s+intrusion(?:\s+(?:concern|pathway))?` |
| `asbestos_lead_paint` | high | real_estate.environmental.acm_lbp | `(?i)\b(asbestos|lead[- ]?based\s+paint|acm|lbp)\s+(?:present|detected|suspect)` |
| `underground_storage_tank` | high | real_estate.environmental.ust | `(?i)\bust\b|underground\s+storage\s+tank|leaking\s+ust` |
| `unpermitted_alteration` | high | real_estate.zoning.unpermitted_alteration | `(?i)unpermitted\s+(?:alteration|addition|conversion|change\s+of\s+use)` |
| `co_expired` | critical | real_estate.zoning.no_co | `(?i)(?:certificate\s+of\s+occupancy|\bco\b)\s+(?:expired|revoked|not\s+issued)` |
| `pending_litigation` | high | real_estate.title.pending_litigation | `(?i)pending\s+(?:litigation|lawsuit|action|condemnation|eminent\s+domain)` |
| `foundation_issue` | high | real_estate.structural.foundation | `(?i)(?:foundation\s+(?:settlement|crack|movement|failure)|structural\s+integr...` |
| `roof_eol` | medium | real_estate.structural.roof | `(?i)roof\s+(?:end[- ]?of[- ]?life|past\s+useful\s+life|active\s+leaks?|deferr...` |
| `ada_noncompliance` | medium | real_estate.accessibility.ada | `(?i)ada\s+(?:noncompliance|violations?|barriers?)|not\s+ada[- ]?compliant` |
| `zoning_variance_lapsed` | high | real_estate.zoning.variance_lapsed | `(?i)variance\s+(?:lapsed|expired|conditions\s+not\s+met)|special\s+(?:use\s+)...` |
| `flood_zone_no_insurance` | medium | real_estate.environmental.flood_zone | `(?i)flood\s+zone\s+[A-Z]\d?(?!.{0,200}(?:flood\s+insurance|nfip))` |

