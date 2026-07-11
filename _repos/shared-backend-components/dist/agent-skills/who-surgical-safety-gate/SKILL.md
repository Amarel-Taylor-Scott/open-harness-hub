---
name: who-surgical-safety-gate
description: Apply WHO Surgical Safety Checklist Sign In before induction.
when_to_use: 'Pipeline kind: review.'
---

# WHO Surgical Safety Checklist gate (Sign In before induction)

Apply the WHO SSC Sign In gate to a pre-induction packet. If any required item is unverified OR any NO-GO is triggered, halt and emit NO-GO.

## Task

Apply WHO Surgical Safety Checklist Sign In before induction.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/who-surgical-safety-gate` v0.1.0
- License: `MIT`
- Industry: healthcare, compliance
- Full source manifest: see `references/manifest.yaml`
