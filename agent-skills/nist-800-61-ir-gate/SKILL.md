---
name: nist-800-61-ir-gate
description: Apply IR playbook gate at incident declaration.
when_to_use: 'Pipeline kind: review.'
---

# NIST 800-61 Incident Response gate

Apply NIST SP 800-61 IR playbook — confirmed data exfil escalates to IC + legal.

## Task

Apply IR playbook gate at incident declaration.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **checklist_gate** — `processor` → `processor/checklist-evaluator`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **knowledge_packs**: `knowledge-pack/technician-checklists`

## Success criteria

- deterministic `$.steps.checklist_gate.output.verdict` == `go`

## Provenance

- Hub component: `pipeline/nist-800-61-ir-gate` v0.1.0
- License: `MIT`
- Industry: cyber, compliance
- Full source manifest: see `references/manifest.yaml`
