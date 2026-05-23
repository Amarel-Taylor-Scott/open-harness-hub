# Personal-info leakage detectors (assistant drafts → wrong audience)

*rule-pack* · `rule-pack/grep-personal-info-leakage` · v0.1.0 · beta

GREP detectors that fire when a personal-assistant DRAFT is about
to be sent to a recipient and contains content the user has
marked private (salary / health / family conflict / mental
health / performance review).

Used by `harness/email-triage-and-draft` as the output-safety
pack — fires AFTER the LLM drafts, BEFORE the user is shown the
draft (or before any autonomous send).

| axis | value |
|---|---|
| industry | personal_productivity, cross_industry |
| capability | safety_gating, anonymization |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `salary_in_draft` | critical | personal.privacy.salary | `(?i)(my salary|i\s+(?:earn|make)\s+\$?[\d,]+|my comp(?:ensation)?\s+(?:is|was...` |
| `health_in_draft` | high | personal.privacy.health | `(?i)(my\s+(?:health|medical|surgery|diagnosis|condition|treatment|therapy|med...` |
| `mental_health` | high | personal.privacy.mental_health | `(?i)(my\s+(?:depression|anxiety|burnout|panic\s+attack)|mental\s+health\s+leave)` |
| `family_conflict` | high | personal.privacy.family | `(?i)(my\s+(?:divorce|separation|custody|estrang(?:ed|ement))|family\s+conflict)` |
| `performance_review_disclosure` | high | personal.privacy.performance | `(?i)(my\s+(?:last\s+)?performance\s+review|my\s+rating\s+(?:was|is)|i\s+recei...` |
| `wrong_audience_for_internal` | critical | personal.privacy.wrong_audience | `(?i)(internal\s+only|confidential|do\s+not\s+share|under\s+nda)\s+[\s\S]{0,20...` |
| `ex_employer_in_draft` | medium | personal.privacy.ex_employer | `(?i)(at\s+my\s+(?:former|previous|prior|last|ex[- ]?employer)|when\s+i\s+(?:w...` |
| `compensation_negotiation` | critical | personal.privacy.job_search | `(?i)(i'?m\s+(?:negotiating|exploring)\s+(?:another|other)\s+(?:offer|opportun...` |
| `weekend_or_after_hours_send` | low | personal.policy.after_hours_send | `(?i)(scheduled\s+to\s+send|sending\s+(?:on|at))\s+(saturday|sunday|after\s+(?...` |

