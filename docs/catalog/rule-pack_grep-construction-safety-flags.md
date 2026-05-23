# Construction safety red-flag detectors (OSHA 1926)

*rule-pack* · `rule-pack/grep-construction-safety-flags` · v0.1.0 · beta

Detectors for OSHA Focus Four + scaffolding + excavation + PPE.

| axis | value |
|---|---|
| industry | construction, construction.safety |
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
| `no_fall_protection_above_6ft` | critical | construction.fall_protection.missing | `(?i)(?:work|working)\s+(?:at|above)\s+(?:height|elevat\w+)(?:\s+(?:of\s+)?(?:...` |
| `unsafe_scaffold` | high | construction.scaffold.deficiency | `(?i)scaffold(?:ing)?\s+(?:missing\s+(?:guardrail|toeboard|midrail)|not\s+insp...` |
| `excavation_no_protective_system` | critical | construction.excavation.no_protective_system | `(?i)excavation\s+(?:over|deeper\s+than|>\s*)\s*5\s*(?:ft|feet|')(?!.{0,200}(?...` |
| `no_competent_person` | high | construction.competent_person.missing | `(?i)(?:no|absent|undesignated)\s+competent\s+person(?:\s+for\s+(?:excavation|...` |
| `energized_work_no_eep` | critical | construction.electrical.energized_no_plan | `(?i)energized\s+(?:electrical\s+)?work(?!.{0,200}(?:electrical\s+energy\s+pla...` |
| `missing_loto` | critical | construction.electrical.no_loto | `(?i)(?:no|absent|missing|skipped)\s+(?:lockout[- ]?tagout|loto)\s+(?:procedur...` |
| `ppe_not_required` | high | construction.ppe.not_required | `(?i)(?:hard[- ]?hat|safety[- ]?glasses|hi[- ]?vis|fall[- ]?harness|gloves)\s+...` |
| `crane_no_signal_person` | high | construction.crane.no_signal_person | `(?i)crane\s+(?:lift|operation)(?!.{0,200}(?:signal\s+person|qualified\s+signa...` |
| `near_miss_not_reported` | medium | construction.reporting.near_miss | `(?i)near[- ]?miss(?:es)?\s+(?:not\s+reported|not\s+logged|verbal\s+only)` |
| `toolbox_talk_skipped` | low | construction.training.toolbox_skipped | `(?i)(?:toolbox\s+talk|pre[- ]?task\s+plan|jha)\s+(?:skipped|missed|not\s+(?:c...` |
| `silica_no_exposure_plan` | high | construction.silica.no_control | `(?i)silica\s+(?:exposure|cutting|grinding|drilling)(?!.{0,200}(?:exposure\s+c...` |
| `confined_space_no_permit` | critical | construction.confined_space.no_permit | `(?i)confined\s+space(?!.{0,200}(?:permit|attendant|rescue|atmospheric\s+(?:te...` |

