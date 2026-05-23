# Space launch + range safety + ITAR/EAR flags

*rule-pack* · `rule-pack/grep-space-launch-flags` · v0.1.0 · beta

Detectors for FAA Part 450 / range-safety / ITAR compliance gaps.

| axis | value |
|---|---|
| industry | space, space.launch, space.export_control, space.orbital |
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
| `expected_casualty_threshold_exceed` | critical | space.ec.exceeded | `(?i)expected\s+casualty\s+(?:figure|estimate|ec)?[\s\S]{0,80}?(?:exceed|above...` |
| `fsa_not_submitted` | critical | space.fsa.missing | `(?i)(?:flight\s+safety\s+analysis|fsa)\s+(?:not\s+(?:submitted|approved|compl...` |
| `itar_foreign_disclosure_no_taa` | critical | space.itar.foreign_disclosure | `(?i)(?:itar|usml|technical\s+data)\s+(?:shared|emailed|transmitted|disclosed)...` |
| `fts_not_qualified` | critical | space.fts.unqualified | `(?i)(?:flight\s+termination\s+system|fts|autonomous\s+termination)\s+(?:not\s...` |
| `hazard_area_not_cleared` | high | space.hazard_area.uncleared | `(?i)(?:launch\s+)?hazard\s+area\s+(?:not\s+(?:cleared|verified)|relied\s+on\s...` |
| `post_mission_disposal_25yr_violation` | high | space.disposal.25yr_exceeded | `(?i)(?:post[- ]?mission\s+disposal|deorbit|orbital\s+lifetime)[\s\S]{0,200}?(...` |
| `two_person_propellant_violation` | critical | space.ground_safety.two_person | `(?i)(?:propellant\s+(?:offload|loading)|fuel\s+loading)\s+(?:performed|conduc...` |
| `range_safety_waiver_undocumented` | high | space.range_safety.undocumented_waiver | `(?i)range\s+safety\s+waiver\s+(?:undocumented|no\s+(?:formal|written)|verbal|...` |
| `ccats_export_classification_missing` | high | space.export.ccats_missing | `(?i)(?:ccats|export\s+classification|eccn\s+9a515)\s+(?:absent|missing|not\s+...` |
| `mpl_insurance_missing` | high | space.mpl.missing | `(?i)(?:maximum\s+probable\s+loss|mpl|financial\s+responsibility)\s+(?:insuran...` |
| `collision_on_launch_uncomputed` | medium | space.col.uncomputed | `(?i)collision[- ]?on[- ]?launch\s+(?:probability\s+)?(?:not\s+(?:computed|eva...` |

