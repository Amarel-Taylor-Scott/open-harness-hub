# PurposeTask dashboard — one truth model, two audiences (Baltor staff + customers)

**Date:** 2026-06-06. **Status:** design (the monitoring/control surface for the CapabilityTask/PurposeTask
layer). The redaction safety core is **built + proven**: `src/baltor/purpose_tasks/projections.py` +
`check_purpose_task_projection_redaction` (flywheel 318). Doctrine:
`docs/standards/capability-task-architecture-doctrine.md`.

## The principle: not observability — a CONTROL SURFACE
This dashboard is the control surface for purpose · evidence · runtime choice · candidate evolution · human
boundary approval · customer trust. It is **projection-only** (reads durable PurposeTask spec + TaskRun +
Evaluation + Promotion + Approval records; never owns/computes truth — same rule as the existing admin/fleet
dashboards). Two views over the SAME data, differing in detail and **redaction**.

## The safety crux (BUILT + PROVEN): deny-by-default redaction
The customer view is built by **explicit allowlist** (`projections.customer_projection`), never by removing a
denylist — so a NEW staff-only field (an internal prompt, a secret, candidate code, a cross-tenant trace, a
redteam payload, builder memory) can **never leak by default**. A second belt, `customer_view_is_clean()`, is a
deep tripwire that fails if any forbidden key surfaces. Proof asserts: one source → two views; no staff-only/
secret/cross-tenant field reaches the customer; the tripwire catches injected leaks; the customer view stays
useful; projection is read-only + deterministic.
- **Customer sees** (allowlist): purpose · contracts summary · connected systems + read/write · allowed AND
  **forbidden** capabilities (the trust floor) · health/freshness · outputs + receipts + source handles ·
  cost/latency trend · pending boundary-approvals · safe change history.
- **Customer NEVER sees**: internal prompts · raw secrets · candidate implementation code · other tenants'
  traces · raw provider decisions · redteam payloads · private builder memory · debug/stack traces.

## Surface A — Staff "Purpose Runtime Control Tower" (`/purpose-tasks?view=staff`)
Cards: **Task Health** (green/yellow/red · failure rate · freshness · eval score) · **Runtime Class** (current
backend · alternatives · last switch + WHY) · **Implementation Lineage** (baseline · candidates · promoted
versions · rollback target) · **Evidence Scorecard** (correctness · source-handles · cost · runtime · safety ·
UI/UX) · **Self-Evolution Workbench** (triggers → diagnosis → candidate generation → eval result → decision) ·
**Policy Gates** (passed/failed/needs-human/boundary-expanded) · **Resource Plan** (tables/queues/object-stores/
secret-refs · temp vs persistent · retention) · **Skill/Template Stack** · **Connected Systems** (up/downstream
· read/write · data class) · **Boundary Approval Queue** · **Cost Arbitrage** (deterministic-path % · browser % ·
LLM % · human-review % — where the cascade savings become visible) · **Audit Trail** (TaskRun · Evaluation ·
Promotion · Rollback · HumanApproval). Plus the **Runtime Decision Timeline** ("why function not K8s, why browser
not HTTP parser, why not candidate v18") and the **Capability Graph** (dependencies · produced/consumed events ·
validators · fallbacks · tenant boundaries → "if this task fails, what breaks? if this source changes, what must
refresh?").

## Surface B — Customer "Capability Assurance Portal" (`/purpose-tasks?view=customer`)
Cards: **What this capability does** · **What it's allowed to touch** (+ the forbidden floor) · **What it
produced recently** (outputs + receipts + supporting sources + what was held out) · **Why the output is trusted**
(impl version · last eval score · source support · policy status · rollback available) · **Health & freshness** ·
**Cost & usage** · **Pending approvals** (new domain/secret/runtime/model/sink — understandable without
engineering context) · **Change history** (safe timeline: "v18 candidate rejected — source-handle coverage 96%;
v19 promoted after 250 shadow runs; runtime moved browser→cloud-run-job, cost −43%") · **Downloadable audit/
receipt**.

## Four top-level surfaces
`/purpose-tasks` (registry · health · runs · candidates · scorecards · approvals · graph · resources) ·
`/task/{id}` (deep task page) · `/experiments` (side-by-side lab: baseline vs candidate · shadow · canary · cost/
fidelity/runtime · promotion gates · rollback) · `/customer-assurance` (the customer portal).

## The projection model (read-only; derive, don't compute truth)
Projections derived from PurposeTaskSpec · TaskRun · EvaluationReport · RuntimeDecision · PromotionDecision ·
RollbackPlan · Telemetry · ResourcePlan · HumanApproval:
`PurposeTask{,Run,Scorecard,Candidate,Approval,Cost,Graph,Resource}Projection` + `PurposeTaskCustomerProjection`.
**Built so far:** `staff_projection` / `customer_projection` / `customer_view_is_clean` (the redaction core);
the rest are the build-prompt's remaining projections + the API routes + the UI.

## Visibility matrix (staff vs customer)
| Data | Staff | Customer |
|---|---|---|
| purpose · contracts · connected systems · allowed/forbidden capabilities | ✓ | ✓ |
| health · outputs · receipts · source handles · cost trend · change history · approvals | ✓ | ✓ (safe summary) |
| candidate code/diffs · runtime-selection internals · logs/traces · skill graph · cost internals · provider decisions · redteam failures · builder memory | ✓ | ✗ |
| raw secrets · internal model prompts · other tenants' data/traces | ✓ (scoped) | ✗ (never) |

## Build status + next
✓ Redaction safety core (`projections.py` + proof, flywheel 318). Next (build prompt
`prompts/baltor-purpose-task-dashboard-and-standard.md`): the remaining projections + the `/api/purpose-tasks/*`
routes (projection/governed-service only; promote/rollback through the gate, never a raw button) + the staff/
customer UI panels + the customer-view redteam (`check_purpose_task_customer_view`: customer can't see staff
data; dashboard can't write truth; promote needs a gate).

*Warrant: clear owner intent ("a new dashboard / way of monitoring that works for Baltor staff AND customers").
One projection-only truth model, two views; customer view deny-by-default (allowlist) — the redaction core is
built + proven; the full UI/routes are the captured build spec. No dashboard truth; promote/rollback gated.*
