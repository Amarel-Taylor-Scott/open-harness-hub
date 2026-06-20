---
name: nfpa-70e-loto-gate
description: Apply LOTO gate before electrical work.
when_to_use: 'Pipeline kind: review.'
---

# NFPA 70E Lockout/Tagout gate

Apply NFPA 70E + OSHA 1910.147 LOTO gate — voltage detected after isolation = re-isolate.

## Task

Apply LOTO gate before electrical work.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/nfpa-70e-loto-gate` v0.1.0
- License: `MIT`
- Industry: energy, compliance
- Full source manifest: see `references/manifest.yaml`
