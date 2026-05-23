# Commercial contract red-flag detectors

*rule-pack* · `rule-pack/grep-contract-red-flags` · v0.1.0 · beta

GREP detectors for the 10 highest-leverage contract red-flag
patterns: uncapped indemnity, unlimited liability, pre-existing
IP assignment, unilateral termination, asymmetric caps, missing
DPA, missing audit rights, missing anti-bribery, change-of-
control without consent, narrow force-majeure.

These trigger reviews — they are not definitive flags. Pair with
`pipeline/contract-clause-review` for full grading.

| axis | value |
|---|---|
| industry | legal, legal.contract, legal.compliance |
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
| `uncapped_indemnity` | critical | legal.uncapped_indemnity | `(?is)indemnif\w*.{0,200}(without limitation|unlimited|no cap|uncapped|any and...` |
| `unlimited_liability` | critical | legal.unlimited_liability | `(?is)(liability|liable)\s+(?:shall be |is )?(?:unlimited|without limit|withou...` |
| `ip_assignment_preexisting` | critical | legal.ip_assignment_preexisting | `(?is)assign(?:s|ment)?\s+(?:to\s+\w+\s+)?(?:all|any)\s+(?:right.{0,30}intelle...` |
| `termination_short_notice` | high | legal.termination_short_notice | `(?is)terminat\w*\s+(?:for convenience|at will|at any time)\s+upon\s+(?:[1-9](...` |
| `no_audit_rights` | high | legal.no_audit_rights | `(?is)(no audit rights|customer may not audit|audit (?:is )?(?:prohibited|not ...` |
| `missing_anti_bribery_warranty` | high | legal.missing_anti_bribery | `(?is)\b(no anti[- ]?bribery|no FCPA|no sanctions (?:representation|warranty))...` |
| `free_assignment` | high | legal.free_assignment | `(?is)may (?:freely )?assign.{0,80}(?:without|no)\s+(?:notice|consent|approval...` |
| `force_majeure_narrow` | medium | legal.force_majeure_narrow | `(?is)force majeure.{0,300}\bonly\b|force majeure.{0,300}(acts of god and war|...` |
| `missing_dpa` | critical | legal.missing_dpa | `(?is)(process|processing).{0,40}personal data(?!.{0,800}(DPA|data processing ...` |
| `asymmetric_cap` | critical | legal.asymmetric_cap | `(?is)Vendor.{0,200}(liability|liable).{0,100}\$?\s*[\d,]+\s+(?:in aggregate)?...` |
| `auto_renewal_short_window` | medium | legal.auto_renewal_short_window | `(?is)auto[- ]?renew\w*.{0,100}(unless.{0,40}notice.{0,40}(\d{1,2})\s*days)(?:...` |
| `exclusivity_perpetual` | high | legal.perpetual_exclusivity | `(?is)(exclusive|sole)\s+(?:supplier|provider|distributor).{0,200}perpetual|pe...` |

