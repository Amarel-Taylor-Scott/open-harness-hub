---
name: msha-preshift-exam
description: Apply MSHA pre-shift / on-shift exam GO/NO-GO gate.
when_to_use: 'Pipeline kind: review.'
---

# MSHA pre-shift exam GO/NO-GO gate

Apply 30 CFR 75.360 pre-shift exam as a deterministic GO/NO-GO gate — methane / O2 / ventilation / roof-rib-face hazards block miner entry.

## Task

Apply MSHA pre-shift / on-shift exam GO/NO-GO gate.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/msha-preshift-exam` v0.1.0
- License: `MIT`
- Industry: mining, compliance
- Full source manifest: see `references/manifest.yaml`
