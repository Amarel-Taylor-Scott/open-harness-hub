# /workflows /baltor-architecture-integrity-and-debt-control (STAGED — focused increments, not one Workflow)

NOT a feature pass. Baltor is now large enough that the main risk is **uncontrolled architectural drift**:
fragile components · monoliths · duplicate runtimes/registries · tools not categorized as
replacements/alternatives · hard-coded provider strings · candidate/fallback/primary roles in business logic ·
poor configuration boundaries · hidden technical debt · mixed concerns · API routes/UI/memory owning truth ·
candidate providers entering the served path without local equivalents · M10 inflation · overlapping pages/
prompts/workflows. **Make those risks measurable, failing, and hard to reintroduce.**

## ARCHITECTURE INTEGRITY CLAUSE (carry in the North Star loop)
Do not allow fragile growth. Every component (module · script · api_route · ui_page · worker · provider ·
schema · config · runtime · proof · doc) must have: **owner · layer · contract · registry entry · proof · docs
· debt status · replacement/fallback/emulator story (if applicable) · split plan (if oversized/legacy)**. Every
tool/provider must be classified in a **replacement graph** (local default · local emulator · candidate ·
fallback · supplement · alternative). Runtime decisions use **typed configuration objects + numeric graph
priorities**, never brittle display strings or hard-coded candidate/fallback branches. **Monoliths, mixed
concerns, M10 inflation, dashboard/API/memory truth, direct provider imports, missing emulators, and
unregistered runtime seams are FAILING checks.**

## Hard rules
No second runtime · no second worker framework · no second provider registry · no second architecture system ·
do not hide debt by renaming · do not weaken proofs to pass · do not mark M10 without behavior + docs + API/UI
(if relevant) + redteam + regression.

## Already in place (C33 guardrails — EXTEND, don't duplicate)
project_spine · file_layout_policy · import_boundaries · runtime_ownership · contract_registry ·
monolith_allowlist · no_duplicate_runtime · no_direct_provider_bypass · dashboard projection-only · ADR coverage.
Numeric preference layer (`preference_graph.py`, status/edge codes) + cloud-agnostic execution shipped 2026-06-06.
Known visible debt to register (not hide): the large `scripts/baltor_admin_demo_server.py`; any duplicate registry.

## Six-plane model (use everywhere)
1 Source/intake (adapters, sync, raw artifacts — NOT truth) · 2 Object/leaf (decomposition, leaves, object
graph — NOT policy) · 3 Governance (verification, reconciliation, freshness, authority) · 4 Execution (worker
routing, backend selection, flywheel, task ledger — NOT truth) · 5 Consumption/export (ContextResponse, native
sidecars, API output — NOT raw compute) · 6 Observability/proof (proofs, receipts, telemetry, review — NOT
mutation/truth).

## Staged increments (each = JSON/code/proof/docs together; flywheel stays green)
- **C-CONSOLIDATE-1:** `architecture/{architecture_integrity_matrix,technical_debt_register,monolith_split_plan,
  module_ownership_matrix,concern_mixing_rules}.json` + proofs `check_architecture_integrity_planes` (every
  component → one plane; no source/exec writes truth; no UI computes truth; no memory writes CanonicalFact),
  `check_technical_debt_register`, `check_monolith_split_plan` (every over-budget file listed w/ target modules +
  expiry; API monolith doesn't own durable truth), `check_mixed_concerns` (forbidden combos: API+raw-DB+truth ·
  UI+durable-mutation · provider-adapter+policy-decision · worker+provider-SDK-import · parser+fact-promotion ·
  memory+CanonicalFact · browser+verified-fact · model+final-ReconciliationDecision · proof+runtime-ownership ·
  config+runtime-branch · dashboard+private-memory+write).
- **C-CONSOLIDATE-2:** numeric provider graph + runtime config-DB object model + `check_no_brittle_provider_string_logic`
  (grep runtime/proofs for `provider==`/`role==`/vendor names; classify OK_DOCS/OK_CONFIG/FIX_RUNTIME/FIX_PROOF/
  FIX_CATALOG; fix the runtime/proof exact-matches). *(provider-graph first increment already shipped — see
  prompts/baltor-numeric-provider-selection-graph.md.)*
- **C-CONSOLIDATE-3:** route/page consolidation — `/offline-demo` primary product page · `/dev` builder/proof
  health · `/fleet` control plane (advanced pages stay, pitch doesn't depend on them).
- **C-CONSOLIDATE-4:** proof grouping + anti-M10-inflation (M10 = behavior + surface + redteam + regression).
- **C-CONSOLIDATE-5:** tool/provider replacement graph — every tool classified alternative/supplement/fallback/
  emulator; `check_tool_replacement_graph` (every slot has local default + emulator; every candidate has a
  replacement edge + proof-to-promote; no uncategorized tool/GitHub ref; no direct provider import outside adapter).
- **C-CONSOLIDATE-6:** monolith split EXECUTION — extract admin-server routes; legacy migration plan.

## Scoreboard + redteam
`docs/status/{technical-debt-scoreboard,architecture-integrity}.md` (open debts by severity · monoliths + split
progress · mixed concerns · string fragility · missing emulators/redteam · candidate-without-equivalent · M10
missing surface · unowned modules · expiring allowlists · top-10 refactors by risk reduction) + proof that every
open/high/overdue debt is reflected + fails when overdue. `check_no_bandaid_architecture` redteam: marking M10
w/o surface · candidate w/o emulator · provider display-string branch · API route writing truth · UI durable
write · memory CanonicalFact · monolith over budget unlisted · second runtime · unregistered command · unowned
module · config hard-coded in runtime · tool ref without replacement-graph entry — all must FAIL safely.

## Acceptance
Integrity matrix + debt register exist · every major component has owner/plane/contract/registry/proofs/docs ·
monolith split plan covers over-budget files · mixed-concern checks fail on new violations · numeric provider
graph + config object model exist · brittle string matching blocked · new provider insertable between priorities
w/o code · tool replacement graph classifies every tool · candidate-without-emulator fails · M10-without-surface
fails · scoreboard exists · no-bandaid redteam passes · all C33 guardrails + offline demo + flywheel GREEN.

*Warrant: clear owner intent ("worried about fragile components, monoliths, mis-categorized replacements, poor
config, tech debt, mixed concerns"). Turn the anxiety into a governed scoreboard, not a feeling. Build as
focused increments; preserve the working foundation (offline demo, CFPB invariant, durable ledger, supervisor).*
