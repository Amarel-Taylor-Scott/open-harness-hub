---
name: haccp-ccp-gate
description: Apply HACCP CCP monitoring gate at production batch release.
when_to_use: 'Pipeline kind: review.'
---

# HACCP CCP monitoring gate

Apply Codex HACCP CCP gate — critical limit exceeded = HOLD product.

## Task

Apply HACCP CCP monitoring gate at production batch release.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/haccp-ccp-gate` v0.1.0
- License: `MIT`
- Industry: food, compliance
- Full source manifest: see `references/manifest.yaml`
