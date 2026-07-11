---
name: security-incident-grading
description: 'Grade a security-incident write-up: extract IOCs + TTPs, evaluate attached
  code for known weaknesses, aggregate a response grade.'
when_to_use: 'Pipeline kind: compound_review.'
---

# Security incident write-up grading (CTI + AppSec chained)

Chains threat-intel IOC review + AppSec code review on incident
write-ups: extracts IOCs/TTPs from the report AND grades any
attached code-of-concern for known vulnerabilities.

## Task

Grade a security-incident write-up: extract IOCs + TTPs, evaluate
attached code for known weaknesses, aggregate a response grade.

## Steps

1. **cti_review** — `pipeline` → `pipeline/threat-intel-ioc-review`
2. **appsec_review** — `pipeline` → `pipeline/code-security-review`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/threat-intel-analyst

## Success criteria

- deterministic `$.steps.cti_review.output.sub_aggregate` is_truthy `None`
- deterministic `$.steps.appsec_review.output.sub_aggregate` is_truthy `None`

## Provenance

- Hub component: `pipeline/security-incident-grading` v0.1.0
- License: `MIT`
- Industry: security, threat_intelligence, security.appsec
- Full source manifest: see `references/manifest.yaml`
