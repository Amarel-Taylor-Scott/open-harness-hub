# Election misinformation / disinformation / deepfake detectors

*rule-pack* · `rule-pack/grep-election-misinformation-flags` · v0.1.0 · beta

Heuristic GREP detectors for common election-misinformation patterns.

| axis | value |
|---|---|
| industry | election_integrity, media, media.factcheck |
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
| `wrong_polling_place_claim` | critical | election.wrong_polling_place | `(?i)(?:voting\s+location|polling\s+place|vote\s+at)\s+(?:changed|moved|reloca...` |
| `wrong_election_date_claim` | critical | election.wrong_date | `(?i)(?:election\s+(?:date|day)|vote)\s+(?:moved|postponed|changed)\s+to\s+(?:...` |
| `fake_ballot_instruction` | high | election.fake_ballot_instruction | `(?i)(?:to\s+vote\s+(?:for|against)|mark\s+ballot)\s+(?:democrat|republican|li...` |
| `voter_id_misinformation` | high | election.voter_id_misinformation | `(?i)(?:must\s+(?:have|bring)|required)\s+(?:photo\s+id|driver'?s?\s+license|p...` |
| `deepfake_artifact_keyword` | high | election.deepfake_artifact | `(?i)(?:lip[- ]?sync\s+(?:off|mismatched)|c2pa\s+(?:missing|absent|stripped)|c...` |
| `coordinated_inauthentic_behavior` | high | election.cib | `(?i)(?:coordinated\s+inauthentic\s+behavior|botnet|sockpuppet\s+network|astro...` |
| `voter_intimidation_text` | critical | election.voter_intimidation | `(?i)(?:do\s+not\s+vote\s+if|stay\s+home|police\s+will\s+be|ice\s+(?:agents?\s...` |
| `fake_official_seal_claim` | medium | election.fake_authority | `(?i)(?:official\s+(?:state|county)\s+election|secretary\s+of\s+state\s+notice...` |
| `incorrect_eligibility_claim` | high | election.fake_eligibility | `(?i)(?:cannot\s+vote|ineligible)\s+if\s+(?:you\s+(?:rent|are\s+a\s+felon|are\...` |
| `voter_roll_pii_in_public` | critical | election.voter_roll_pii_leak | `(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)` |

