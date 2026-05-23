# Nuclear safety / NRC / IAEA flags

*rule-pack* · `rule-pack/grep-nuclear-safety-flags` · v0.1.0 · beta

Detectors for nuclear-safety findings.

| axis | value |
|---|---|
| industry | nuclear, nuclear.nrc, nuclear.iaea |
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
| `lco_exceedance` | critical | nuclear.lco.exceedance | `(?i)(?:lco|limiting\s+condition\s+for\s+operation)\s+(?:exceeded|exceedance|v...` |
| `ler_unfilled` | critical | nuclear.ler.unfilled | `(?i)(?:ler|licensee\s+event\s+report)\s+(?:not\s+(?:filed|submitted)|past\s+6...` |
| `scram_unexplained` | critical | nuclear.scram.unexplained | `(?i)(?:unplanned|unexpected|manual)\s+(?:scram|trip|reactor\s+shutdown)(?!.{0...` |
| `tech_spec_surveillance_overdue` | high | nuclear.tech_spec.surveillance_overdue | `(?i)(?:tech[- ]?spec|technical\s+specification)\s+surveillance\s+(?:past\s+du...` |
| `physical_security_breach` | critical | nuclear.physical_security.breach | `(?i)(?:vital\s+area|protected\s+area)\s+(?:breach|intrusion|unauthorized\s+en...` |
| `snm_inventory_discrepancy` | critical | nuclear.snm.inventory_discrepancy | `(?i)(?:snm|special\s+nuclear\s+material)\s+inventory\s+(?:discrepancy|miscoun...` |
| `rop_yellow_red_finding` | high | nuclear.rop.yellow_red | `(?i)(?:rop|reactor\s+oversight)\s+(?:finding\s+)?(?:yellow|red)|significance\...` |
| `iaea_safeguards_irregularity` | high | nuclear.iaea.safeguards | `(?i)iaea\s+safeguards\s+(?:irregularity|finding|noncompliance|access\s+denied)` |
| `fitness_for_duty_failure` | high | nuclear.ffd.failure | `(?i)fitness[- ]?for[- ]?duty\s+(?:test\s+)?(?:fail|positive)|10\s+cfr\s+26\s+...` |
| `operator_license_lapsed` | high | nuclear.operator.license_lapsed | `(?i)(?:operator|senior\s+operator|sro)\s+license\s+(?:lapsed|expired|inactive)` |
| `training_recertification_overdue` | medium | nuclear.training.overdue | `(?i)(?:training|recertification|requalification)\s+(?:overdue|past\s+due|expi...` |
| `spent_fuel_pool_level` | critical | nuclear.spent_fuel.parameter | `(?i)spent\s+fuel\s+pool\s+(?:level|temperature)\s+(?:below|above|exceeds?)\s+...` |

