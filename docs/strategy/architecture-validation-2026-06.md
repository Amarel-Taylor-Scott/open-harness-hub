# Architecture adversarial validation — 2026-06-21

Three independent adversarial reviewers (overlap, confusion/contradictions, flexibility/lock-in) audited the portfolio
against the canonical sources. Companion to the visual map: `docs/strategy/architecture-map.md` +
`dist/architecture/index.html`.

## Verdict
The architecture is **technically sound and LOCKED + enforced** — the dependency law (Baltor → Teleon → OpenHarnessHub),
plane separation, and the surface-family roster are all green in code. **The drift is in the NARRATIVE prose and in the
Open\*Hub roster's overlaps, not in the enforced core.** Said plainly: a locked architecture, an unlocked *story*.

**On LOCKED memories:** the review CONFIRMS the locked decisions (3-layer model; parent = holding brand only) are
**correct** — the contradictions lived in stale docs that disagreed with them. So we reconcile the docs *to* the locked
memories (the locked decision is the warrant), and we *sharpen* the locked memory additively (truth-vs-efficiency moat
split; "Baltor powered by Teleon") so prose can't drift again.

## Findings by severity

### Narrative / clarity
- **BLOCKER — "two products" vs "three layers":** `master-goal.md` (North Star v2: OHH funnel + verified-context
  service) contradicts the LOCKED 3-layer model (`teleon-baltor-openharnesshub-portfolio.md`, `surface_map.json`,
  `portfolio_dependency_law.json`). → **RECONCILED** (banner on `master-goal.md`; the 3-layer model wins).
- **MAJOR — parent positioned as "the trust layer"** (a product value-prop) vs the LOCKED "holding brand, owns no
  runtime/customer data." → **FIXED** in `surface_map.json` (now holding-brand language).
- **MAJOR — Baltor's wedge hid "powered by Teleon"** (the YC pitch reads Baltor as independent). → **FIXED** in
  `surface_map.json` (and to add to the YC prep doc).
- **MAJOR — both Baltor and Teleon claim "governance" as the moat.** → **PROPOSE**: lock the split — *Baltor governs
  what becomes TRUE; Teleon governs what becomes EFFICIENT (the descent brain).*
- **MAJOR — `surface_map.json` lists only 1 of 22 Open\*Hubs.** → addressed by the new architecture map (full roster);
  PROPOSE referencing the canonical roster from the surface map.
- **MINOR** — `ContextIsEverything` status (rollback vs Baltor origin line; code slug still `contextiseverything`);
  `PurposeTask` vs `CapabilityTask` naming not enforced in surface_map / YC materials.

### Overlap / boundaries
- **MAJOR — the 5 Baltor method-hubs** (Open{Reconciliation,Hardening,Enrichment,Optimization,Verification}Hub)
  duplicate Baltor's own pipeline (ingest→reconcile→harden→enrich→optimize→verify→serve). Same spine claimed by both
  the product and 5 registry surfaces, no clear API boundary. → **PROPOSE (owner)**: pure-registry vs pure-workflow.
- **MAJOR — teleon-demos vs OpenHarnessHub both claim "proof."** → **PROPOSE (owner)**: define the proof-authority gate.
- **MAJOR — OpenContextHub vs OpenCurrentContextHub** overlap on the source/freshness input. → **PROPOSE (owner)**: an
  operational gate (truth ≠ freshness signal).
- **MAJOR — OpenSkillToTool vs OpenToolToSkillHub** (forward vs bidirectional). → **PROPOSE (owner)**: merge path.
- **MINOR** — rejected hubs (OpenEvalHub/OpenGuardrailHub/OpenDatasetHub) held in prose limbo; Teleon runtime vs
  OpenRoutingHub framing.

### Flexibility / lock-in
- **HIGH — surface `layer` + the 22-hub roster are scattered** across `surface_map.json`, `portfolio_connection_map.json`,
  `open_hubs_bridge_graph.json`, `repo_hub_mapping_policy.json`, `identity_realm_registry.json` — no single canonical
  source. → **FILE**: one canonical roster + a consistency check; add `layer` from that one source.
- **MEDIUM — execution-provider factory is a hardcoded dispatcher** (`execution_providers/factory.py`), not
  registry-driven → a new backend is a code edit. → **FILE**: registry + `importlib`.
- **MEDIUM — ledger + blackboard are SQLite-locked** while Git is cleanly ported (`git_backend_port.py`). → **FILE**:
  a `StorageBackendPort` so customer-managed Postgres/DuckDB is a config swap.
- **MEDIUM — tenant id `baltor-internal` hardcoded ~9×.** → **FILE**: one constant.
- **LOW — search-provider selection half-wired** (registry exists; `real_steps.py` hardcodes Wikipedia/Ollama). → **FILE**.

## Reconciliation status
- **DONE (this change):** parent = holding-brand prose; Baltor "powered by Teleon"; `master-goal.md` 3-layer banner.
- **PROPOSE (owner-gated, filed to the backlog):** the hub-overlap merges; the moat-language split; the final
  "two-products vs three-layers" ratification.
- **FILE (engineering, filed to the backlog):** single-source layer/roster + check; factory→registry;
  StorageBackendPort; tenant constant; search-selector.

These are filed into `data/dev-intel/proposals.jsonl` (review via `./loop review`); the loop's `yc` + agent tracks work
them down. Owner-gated items wait for you.

## RESOLVED 2026-06-21 (owner-confirmed; explicit permission to edit locked memories)
The owner ratified the two biggest items + sharpened the product model:
- **Moat split — LOCKED:** *Baltor governs what becomes TRUE; Teleon governs what becomes EFFICIENT (the descent brain).*
  Applied to `brand.json` (brand_laws), `surface_map.json`, the portfolio doc, and the locked memory.
- **Method-hub boundary — LOCKED:** the 5 Baltor method-hubs are STORE components (method SPECS only; discovery≠trust);
  Baltor SELECTS (via Teleon) → RUNS on customer data → OWNS the truth. Spec in the store, execution+truth in Baltor.
- **Product model sharpened (owner):** **Teleon is its OWN product** (program capabilities in plain text → auto-adapt to
  cheapest-bounded within guardrails), not only Baltor's runtime. **Baltor is the MANAGED-context product**
  (company/department/initiative-wide). **The open ecosystem is a STORE** of reusable components both consume
  (context/tools/models/steps/DAG/reconciliation+robustness+enrichment rules/modules). Code-import law stays
  Baltor→Teleon→OHH; the store is consumed at the content level by both. surface_map / brand / portfolio doc / master-goal
  / the architecture map all reconciled to match; guards green.
- **Still open (owner):** the remaining hub overlaps (teleon-demos vs OpenHarnessHub proof authority; OpenContextHub vs
  OpenCurrentContextHub; SkillToTool merge) + the engineering flexibility items remain filed for the loop.
