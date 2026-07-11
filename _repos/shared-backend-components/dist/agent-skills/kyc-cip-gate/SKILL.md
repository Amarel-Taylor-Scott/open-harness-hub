---
name: kyc-cip-gate
description: Apply CIP/CDD gate before account opening.
when_to_use: 'Pipeline kind: review.'
---

# KYC/CIP onboarding gate (BSA + USA PATRIOT §326)

Apply CIP 4-element + OFAC + PEP + beneficial-ownership gate before account opening. OFAC hit + cannot-verify-identity = NO-GO.

## Task

Apply CIP/CDD gate before account opening.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/kyc-cip-gate` v0.1.0
- License: `MIT`
- Industry: finance, compliance
- Full source manifest: see `references/manifest.yaml`
