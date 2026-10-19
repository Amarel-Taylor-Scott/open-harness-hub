---
name: pssr-startup-gate
description: Apply PSM Pre-Startup Safety Review GO/NO-GO gate.
when_to_use: 'Pipeline kind: review.'
---

# PSM Pre-Startup Safety Review (PSSR) gate

Apply 29 CFR 1910.119(i) PSSR as a deterministic gate before unit start-up after maintenance — open Cat-A items / unresolved PHA / training gaps block hydrocarbon introduction.

## Task

Apply PSM Pre-Startup Safety Review GO/NO-GO gate.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/pssr-startup-gate` v0.1.0
- License: `MIT`
- Industry: energy, compliance
- Full source manifest: see `references/manifest.yaml`
