---
name: faa-preflight-gate
description: Apply FAA Before-Takeoff Checklist + Takeoff Briefing.
when_to_use: 'Pipeline kind: review.'
---

# FAA Part 91 Before-Takeoff gate

Apply the FAA before-takeoff checklist as a deterministic GO/NO-GO gate.

## Task

Apply FAA Before-Takeoff Checklist + Takeoff Briefing.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/faa-preflight-gate` v0.1.0
- License: `MIT`
- Industry: aviation, compliance
- Full source manifest: see `references/manifest.yaml`
