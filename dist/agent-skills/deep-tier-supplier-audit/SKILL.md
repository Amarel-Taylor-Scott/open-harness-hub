---
name: deep-tier-supplier-audit
description: Given a tier-1 supplier ID + a supplier-graph reference, traverse down
  to tier 4+, grade each tier's disclosures, surface audit-gaps and high-risk-corridor
  flags, return a chain-wide compliance report.
when_to_use: 'Pipeline kind: agent_loop.'
---

# Deep-tier (T1→T4+) supplier audit with traceability

Multi-step audit pipeline that walks a supplier graph from tier-1
(direct supplier) down to tier-3 and tier-4+ (raw-material origin
/ sub-sub-contractors). At each tier:
 1. Resolve supplier identity against the supplier registry.
 2. Run `pipeline/supplier-policy-grading` on that tier's disclosure.
 3. Identify audit-gaps (typically appear at T≥3).
 4. Surface high-risk-corridor flags (Xinjiang, Mae Sot, Sialkot, etc.).
 5. Aggregate findings, route the highest-severity to the
    compliance team, the rest to the supplier-of-record for
    remediation.

This is the shape EU CSDDD Art. 5 mandates as of 2026 — "risk-based
due diligence covering the entire chain of activities, including
established business relationships."

## Task

Given a tier-1 supplier ID + a supplier-graph reference, traverse
down to tier 4+, grade each tier's disclosures, surface audit-gaps
and high-risk-corridor flags, return a chain-wide compliance
report.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **walk_chain** — `processor` → `processor/iterative-revise-loop`
3. **aggregate_audit_gaps** — `processor` → `processor/multi-vector-fusion`
4. **escalate_high_severity** — `processor` → `processor/escalate-human-review`
5. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/esg-auditor
- **model_adapter**: adapter/ollama-default

## Success criteria

- rubric `rubric/esg-supplier-compliance-v1` threshold 0.6

## Provenance

- Hub artifact: `pipeline/deep-tier-supplier-audit` v0.1.0
- License: `MIT`
- Industry: esg, supply_chain, compliance
- Full source manifest: see `references/manifest.yaml`
