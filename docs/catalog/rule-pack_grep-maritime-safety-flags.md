# Maritime safety red-flag detectors (SOLAS / MARPOL / ISM)

*rule-pack* · `rule-pack/grep-maritime-safety-flags` · v0.1.0 · beta

Detectors for vessel + crew + management deficiencies.

| axis | value |
|---|---|
| industry | maritime, maritime.safety |
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
| `lifeboat_deficient` | critical | maritime.lsa.lifeboat | `(?i)(?:lifeboat|life[- ]?raft|davit)\s+(?:inoperative|deficient|missing|past\...` |
| `epirb_battery_expired` | critical | maritime.radio.epirb | `(?i)(?:epirb|emergency\s+position[- ]?indicating\s+radio\s+beacon)\s+(?:batte...` |
| `ism_doc_smc_invalid` | critical | maritime.ism.doc_smc_invalid | `(?i)(?:document\s+of\s+compliance|\bdoc\b|safety\s+management\s+certificate|\...` |
| `no_dpa` | high | maritime.ism.no_dpa | `(?i)(?:no|absent|undesignated)\s+(?:designated\s+person\s+ashore|dpa)|dpa\s+(...` |
| `oil_record_book_gap` | critical | maritime.marpol.orb_gap | `(?i)(?:oil\s+record\s+book|\borb\b)\s+(?:gap|missing\s+entries|incomplete|bac...` |
| `garbage_record_book_gap` | high | maritime.marpol.garbage_book | `(?i)garbage\s+record\s+book\s+(?:gap|missing|not\s+maintained)|marpol\s+annex...` |
| `ballast_water_treatment_gap` | high | maritime.marpol.bw_treatment | `(?i)ballast\s+water\s+(?:treatment|management)\s+(?:bypass|inoperative|noncom...` |
| `ecdis_outdated_chart` | high | maritime.navigation.ecdis | `(?i)(?:ecdis\s+chart|enc)\s+(?:outdated|past\s+update|not\s+current)|charts?\...` |
| `sopep_gap` | high | maritime.marpol.sopep | `(?i)(?:shipboard\s+oil\s+pollution\s+emergency\s+plan|sopep)\s+(?:missing|not...` |
| `stcw_certificate_expired` | critical | maritime.crew.stcw_expired | `(?i)(?:stcw\s+certificate|certificate\s+of\s+competency|coc)\s+(?:expired|inv...` |
| `work_rest_hours_violation` | high | maritime.crew.work_rest | `(?i)(?:work[- ]?rest|mlc\s+2006|hours\s+of\s+rest)\s+(?:violation|noncomplian...` |
| `isps_security_breach` | high | maritime.security.isps | `(?i)(?:isps|international\s+ship\s+and\s+port\s+facility\s+security)\s+(?:bre...` |

