# /workflows /baltor-purpose-task-dashboard-and-standard (STAGED — the dual-audience control surface)

Build the PurposeTask dashboard (Baltor STAFF + CUSTOMER views over one truth model) on top of the CTS/
PurposeTask runtime. Design: `docs/architecture/purpose-task-dashboard-staff-and-customer.md`. The redaction
safety core is **already built + proven** (`src/baltor/purpose_tasks/projections.py` +
`check_purpose_task_projection_redaction`, flywheel 318).

> **Core principle:** CapabilityTask stays stable · Implementation evolves · Runtime changes · Evidence decides ·
> Policy gates promotion · Humans approve boundary expansion. **Dashboard rules:** projection-only (no dashboard
> truth); customer view deny-by-default (allowlist redaction — already built); promote/rollback go through the
> gate, never a raw button; customers never see staff internals/secrets/cross-tenant data. No second worker
> framework / durable ledger / provider registry. Build on FleetLedger + the execution selector + Parallel-Path
> Engine. Focused increments; never concurrent with another repo-mutating workflow.

## Build (each = schema/code/proof/docs; reuse the supervisor_projection + admin-server route patterns)
- **P1 — remaining contracts:** `schemas/purpose_tasks/{PurposeTaskRun,PurposeTaskImplementation,
  PurposeTaskRuntimeClass,PurposeTaskEvaluation,PurposeTaskPromotion,PurposeTaskRollback,TaskOrientation,
  PurposeTaskProjection,PurposeTaskCustomerProjection}.v1` (register in contract_registry). `PurposeTaskSpec.v1`
  + the runtime-class vocabulary already exist.
- **P2 — registries:** `architecture/{purpose_task_registry,purpose_task_runtime_classes(exists),
  purpose_task_success_criteria,purpose_task_promotion_policies,purpose_task_boundary_expansion_policies}.json`.
- **P3 — projections:** extend `src/baltor/purpose_tasks/projections.py` (staff/customer redaction DONE) with
  the remaining derived projections (run · scorecard · candidate · approval · cost · graph · resource). Build on
  the existing supervisor_projection pattern.
- **P4 — API (projection + governed-service only):** GET `/api/purpose-tasks[/<id>[/runs|scorecards|candidates|
  promotions|orientation|customer]]` + POST run-local / run-side-by-side / promote-candidate / rollback. The
  `/customer` route returns `customer_projection` and MUST pass `customer_view_is_clean()` before sending.
  promote/rollback call the governed promotion gate (Parallel-Path Engine), never mutate directly.
- **P5 — UI:** `/purpose-tasks?view=staff` (the Control Tower cards: health · runtime class + decision timeline ·
  implementation lineage · evidence scorecard · self-evolution workbench · policy gates · resource plan · skill/
  template stack · connected systems · capability graph · boundary-approval queue · cost arbitrage · audit trail)
  + `/purpose-tasks?view=customer` (the Assurance Portal cards: what-it-does · what-it-touches + forbidden floor ·
  recent outputs + receipts + held-out · why-trusted · health/freshness · cost · pending approvals · change
  history · downloadable receipt). Keep the dark/compact aesthetic; projection-only; honest statuses.
- **P6 — redteam:** `check_purpose_task_customer_view` / `check_purpose_task_dashboard_redteam` — all FAIL safely:
  customer sees staff/candidate/secret/cross-tenant data · dashboard writes truth · promote without a gate ·
  rollback target missing · runtime switched to a disallowed class without a decision receipt · self-evolution
  changes purpose/permissions/success-criteria via the UI.
- **P7 — proofs + regression:** check_purpose_task_{registry,runtime_selection(CTS-1),side_by_side,
  promotion_gate,orientation,dashboard_api,dashboard_ui,customer_view,redteam,full_stack}; REGRESS
  demo_offline_full_baltor · check_baltor_full_stack_perfect · check_durable_fleet_ledger ·
  check_live_supervisor_full_stack · check_no_direct_provider_bypass · `baltor_flywheel.py --once`.

## Acceptance
PurposeTask contracts + registry exist · local PurposeTasks run · runtime selection works (CTS-1) · candidate
runs side-by-side · evidence scorecard works · promotion gate blocks unsafe changes · boundary expansion needs
human approval · TaskOrientation works · STAFF dashboard exists · CUSTOMER dashboard exists + leaks nothing
staff-only (proven) · dashboard computes no truth · redteam fails safely · offline demo + flywheel GREEN.

*Warrant: clear owner intent (a new dashboard for staff AND customers monitoring the self-adaptive PurposeTask
layer). One projection-only truth model, two redacted views (customer = allowlist deny-by-default, built+proven);
promote/rollback gated; no dashboard truth; reuse FleetLedger + execution selector + Parallel-Path Engine.*
