# Deep-tier (T1→T4+) supplier audit with traceability

*pipeline* · `pipeline/deep-tier-supplier-audit` · v0.1.0 · experimental

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

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
| capability | evaluation, extraction, verification, agent_loop |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a tier-1 supplier ID + a supplier-graph reference, traverse
down to tier 4+, grade each tier's disclosures, surface audit-gaps
and high-risk-corridor flags, return a chain-wide compliance
report.

**pipeline_kind:** `agent_loop`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `walk_chain` | processor | `processor/iterative-revise-loop` | — |
| 3 | `aggregate_audit_gaps` | processor | `processor/multi-vector-fusion` | — |
| 4 | `escalate_high_severity` | processor | `processor/escalate-human-review` | — |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | — |

