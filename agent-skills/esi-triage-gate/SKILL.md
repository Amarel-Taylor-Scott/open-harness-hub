---
name: esi-triage-gate
description: Apply ESI triage gate at ED registration.
when_to_use: 'Pipeline kind: review.'
---

# ESI 5-Level Triage gate (ER)

Apply AHRQ ESI v4 triage algorithm — danger-zone vitals at ESI 3 require upgrade to ESI 2.

## Task

Apply ESI triage gate at ED registration.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/esi-triage-gate` v0.1.0
- License: `MIT`
- Industry: healthcare, compliance
- Full source manifest: see `references/manifest.yaml`
