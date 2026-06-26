---
name: itil-change-gate
description: Apply ITIL change-enablement gate before production change.
when_to_use: 'Pipeline kind: review.'
---

# ITIL Change Enablement gate

Apply ITIL 4 change-enablement runbook as deterministic gate — CAB approval + backout plan + validation criteria are GO requirements.

## Task

Apply ITIL change-enablement gate before production change.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/itil-change-gate` v0.1.0
- License: `MIT`
- Industry: it, compliance
- Full source manifest: see `references/manifest.yaml`
