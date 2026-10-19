---
name: trid-loan-gate
description: Apply TRID gate before mortgage consummation.
when_to_use: 'Pipeline kind: review.'
---

# TRID Loan Estimate + Closing Disclosure gate

Apply Reg Z TRID timing + tolerance gate before mortgage consummation — CD timing miss = NO-GO + re-issue.

## Task

Apply TRID gate before mortgage consummation.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/trid-loan-gate` v0.1.0
- License: `MIT`
- Industry: finance, compliance
- Full source manifest: see `references/manifest.yaml`
