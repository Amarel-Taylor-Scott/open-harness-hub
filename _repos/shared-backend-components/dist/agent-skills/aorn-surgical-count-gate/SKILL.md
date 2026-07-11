---
name: aorn-surgical-count-gate
description: Apply AORN surgical count gate before OR transport.
when_to_use: 'Pipeline kind: review.'
---

# AORN Surgical Count GO/NO-GO gate

Apply AORN Sponge/Sharp/Instrument count gate before patient leaves OR — discrepancy requires intra-op imaging.

## Task

Apply AORN surgical count gate before OR transport.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/aorn-surgical-count-gate` v0.1.0
- License: `MIT`
- Industry: healthcare, compliance
- Full source manifest: see `references/manifest.yaml`
