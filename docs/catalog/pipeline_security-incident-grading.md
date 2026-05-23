# Security incident write-up grading (CTI + AppSec chained)

*pipeline* · `pipeline/security-incident-grading` · v0.1.0 · experimental

Chains threat-intel IOC review + AppSec code review on incident
write-ups: extracts IOCs/TTPs from the report AND grades any
attached code-of-concern for known vulnerabilities.

| axis | value |
|---|---|
| industry | security, threat_intelligence, security.appsec |
| capability | extraction, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Grade a security-incident write-up: extract IOCs + TTPs, evaluate
attached code for known weaknesses, aggregate a response grade.

**pipeline_kind:** `compound_review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `cti_review` | pipeline | `pipeline/threat-intel-ioc-review` | — |
| 2 | `appsec_review` | pipeline | `pipeline/code-security-review` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

