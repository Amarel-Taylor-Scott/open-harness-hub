# Teleon

> Teleon turns functions, jobs, workers, and automations into self-adaptive capabilities.

**Kind:** Teleon.dev · purpose-driven runtime

**Audience:** Platform-engineering, AI-infrastructure, DevOps/SRE, and automation teams.

## What it is
- Intent-native, eval-gated, self-adaptive compute.
- A purpose-defined runtime built around the CapabilityTask / PurposeTask object.

## What it is not
- Not a generic AI-agent deployment product.
- Not a replacement for Kubernetes.
- Not a replacement for cloud functions.
- Not unbounded self-modifying code.

## Owns
- CapabilityTask / PurposeTask runtime
- Runtime selection
- Implementation candidates
- Evidence ledger
- Promotion + policy gates
- Boundary approvals

## Does not own
- Governed context truth (that is Baltor)
- The open skill registry (that is OpenHarnessHub)

## Relationship
Teleon runs and evolves capabilities. Baltor consumes Teleon through the PurposeTaskProviderPort; Teleon returns evidence/candidate/result, never Baltor truth. Teleon consumes templates, skills, and eval packs from OpenHarnessHub.

*Canonical source: scripts/portfolio_lib.py (edit there; this mirror is for human review).*
