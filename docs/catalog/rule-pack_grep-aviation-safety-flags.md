# Aviation safety incident flags (NTSB / FAA / HFACS)

*rule-pack* · `rule-pack/grep-aviation-safety-flags` · v0.1.0 · beta

Detectors for aviation-incident-report red flags.

| axis | value |
|---|---|
| industry | aviation, aviation.safety |
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
| `cfit_indicator` | critical | aviation.cfit | `(?i)(?:controlled\s+flight\s+into\s+terrain|cfit\b)|terrain\s+impact` |
| `loci_indicator` | critical | aviation.loc_i | `(?i)loss\s+of\s+control[- ]?(?:in[- ]?flight)?|\bloc[- ]?i\b|stall.{0,40}spin` |
| `fuel_exhaustion` | critical | aviation.fuel | `(?i)fuel\s+(?:exhaustion|starvation|mismanagement)` |
| `runway_incursion` | high | aviation.runway_incursion | `(?i)runway\s+incursion|category\s+[abc]\s+incursion` |
| `no_sms_documentation` | high | aviation.sms_missing | `(?i)(?:no|absent)\s+sms\s+documentation|sms\s+(?:not\s+implemented|noncomplia...` |
| `ground_school_lapsed` | high | aviation.training_lapsed | `(?i)(?:recurrent\s+training|ground\s+school|line\s+check)\s+(?:lapsed|overdue...` |
| `maint_log_gap` | critical | aviation.maintenance_gap | `(?i)maintenance\s+log\s+(?:gap|missing\s+entries|incomplete)|airworthiness\s+...` |
| `crew_fatigue` | high | aviation.fatigue | `(?i)(?:crew\s+fatigue|inadequate\s+(?:crew\s+)?rest|duty\s+time\s+exceeded|11...` |
| `weather_decision` | high | aviation.weather_decision | `(?i)(?:weather|imc|ifr)\s+(?:into|despite|exceeded)\s+(?:minimums|limits)|vfr...` |
| `tcas_ra_response` | critical | aviation.tcas_ra_noncompliance | `(?i)tcas\s+(?:ra|resolution\s+advisory)\s+(?:not\s+complied|inverse|opposite)` |
| `uncontained_engine_failure` | critical | aviation.uncontained_engine | `(?i)(?:uncontained|in[- ]?flight)\s+engine\s+(?:failure|shutdown\s+with\s+dam...` |
| `missed_pirep` | low | aviation.no_pirep | `(?i)(?:no|absent)\s+pirep\s+(?:filed|reported)|pilot\s+report\s+not\s+submitted` |

