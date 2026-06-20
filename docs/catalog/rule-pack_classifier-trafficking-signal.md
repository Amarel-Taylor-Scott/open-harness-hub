# Trafficking-signal classifier (UGC second-stage)

*rule-pack* · `rule-pack/classifier-trafficking-signal` · v0.1.0 · experimental

Second-stage classifier rules invoked after
`rule-pack/grep-human-trafficking-ugc-flags` fires. The GREP pack
catches surface-level cues; this classifier pack is a labeled-example
bundle for the LLM judge to weigh whether the post fits a
recognized trafficking typology (Polaris Project taxonomy of 25
types, condensed here to the most-frequent UGC-platform-visible
cases).

Used by `pattern/two-stage-extract-then-judge`: stage-1 extracts
every relevant field (advertised service, claimed identity, control
markers, transit cues, contact pathway); stage-2 (this pack) scores
the extracted JSON against the typology and emits a confidence per
typology slot. Composite confidence flowing into
`pattern/critical-tier-output-override` controls the routing.

| axis | value |
|---|---|
| industry | compliance, media, humanitarian, humanitarian.trafficking |
| capability | classification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | dated |
| license | MIT |



**family:** `classifier`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `sex_trafficking_escort_services` | critical | polaris.t1.sex.escort | `` |
| `sex_trafficking_illicit_massage` | high | polaris.t3.sex.massage | `` |
| `sex_trafficking_residential_brothel` | high | polaris.t7.sex.residential | `` |
| `labor_trafficking_domestic_work` | high | polaris.t13.labor.domestic | `` |
| `labor_trafficking_agriculture` | high | polaris.t14.labor.agriculture | `` |
| `labor_trafficking_construction` | high | polaris.t15.labor.construction | `` |
| `labor_trafficking_hospitality_food` | high | polaris.t16.labor.foodservice | `` |
| `labor_trafficking_fishing_maritime` | critical | polaris.t19.labor.fishing | `` |
| `victim_disclosure_help_seeking` | critical | polaris.victim.disclosure | `` |
| `csam_suspicion_route_to_ncmec` | critical | ncmec.referral.csam_route | `` |

