# Portfolio infrastructure topology — close, but separable

**Status:** owner-directed 2026-06-06; parent brand updated 2026-06-09. Canonical configs: `architecture/company_portfolio_map.json` (the
company boundary model) + `architecture/portfolio_dependency_law.json` (the import law) + 
`architecture/domain_brand_risk_register.json` (brand risk). Enforced by
`scripts/check_company_portfolio_boundaries.py` + `scripts/check_portfolio_dependency_law.py`. Portfolio
overview: [`teleon-baltor-openharnesshub-portfolio.md`](../strategy/teleon-baltor-openharnesshub-portfolio.md).
The legal/code slug `contextiseverything` is preserved as an identifier; the
current displayed parent brand is **AI Done Right** (`aidoneright.dev`).

## The principle
> **Co-located for latency/dev-speed · contract-separated for product clarity · account-separated for
> security/spinout · data-separated for trust · brand-separated for customer clarity.**

The goal: Teleon, Baltor, and OpenHarnessHub run in the **same dev environment today**, the **same region /
cloud org tomorrow**, and **separate accounts / repos / companies later** — without code surgery.

## The portfolio (HoldCo = AI Done Right)
- **AI Done Right** (HoldCo; code slug `contextiseverything`) — portfolio/brand/research/IP. **Owns no runtime code, no customer data.**
- **Teleon** (`teleon.dev`) — the purpose-driven runtime SaaS.
- **Baltor** (`baltor.ai`) — the governed-context applied product, a **tenant** of Teleon.
- **OpenHarnessHub** (`openharnesshub.io`, with legacy redirects where applicable) — the open ecosystem + the open CapabilityTask spec.
- **Open*Hub family** — the broader registry surface family used for open
  discovery and private-first standards/lead-gen. The design handoff currently
  includes 21 Open*Hubs; `company_portfolio_map.json` tracks the company/data
  boundary subset, not every prototype surface.

## "Located close" means five concrete things
1. **Same region** — low-latency Baltor→Teleon calls (Baltor is a high-frequency caller).
2. **Private connectivity** — PrivateLink / Private Service Connect / VPC peering / service mesh; **not** the
   public internet for prod service-to-service.
3. **Shared identity root, separate service identities** — one SSO/identity foundation, but
   `teleon-runtime-service` / `baltor-context-service` / `openharnesshub-registry-service` are distinct. **No
   shared god token.**
4. **Shared observability schema, separate telemetry stores** — same event/trace vocabulary (CloudEvents
   envelopes, OTel fields, CapabilityTask IDs), but each product keeps its own telemetry store.
5. **Shared local development, separate deployability** — develop together locally; each deploys alone. Baltor
   runs with an **embedded-local Teleon** provider if the Teleon service is unavailable (graceful degrade).

## Separation levers (so a clean cut stays cheap)
1. A **versioned API contract** between products is the *only* coupling (the Teleon API / `PurposeTaskProviderPort`).
2. **No shared production database.** Each product owns its store; integrate via API + events, never a shared schema.
3. **No cross-boundary code imports** — enforced by `check_portfolio_dependency_law.py` (Baltor → Teleon → OHH only).
4. **Separate identity / billing / IaC** per product.
5. **Graceful local fallback** if a dependency is down (cloud-defer-only-after-local-equivalent, applied at the
   company boundary).

## Cloud org / account layout (cloud-agnostic principle; one parent org, separate accounts)
**AWS** — Organization `AI-Done-Right` → Shared-Services · Teleon-Dev · Teleon-Prod · Baltor-Dev ·
Baltor-Prod · OpenHarnessHub · Security/Audit accounts. Connectivity via Transit Gateway / VPC peering /
PrivateLink only where needed; no shared prod DB; cross-account only via role assumption + audit.
**GCP** — Org → folders Shared / Teleon / Baltor / OpenHarnessHub / Security; projects `teleon-dev`,
`teleon-prod`, `baltor-dev`, `baltor-prod`, `ohh-prod`; Shared VPC optional; Private Service Connect where needed.
**Azure** — Tenant → management groups Shared / Teleon / Baltor / OpenHarnessHub.
Separate **billing labels / cost centers** from day one regardless of cloud.

## Data boundaries (the trust pillar — enforced)
- **Teleon stores:** CapabilityTask specs, task runs, runtime decisions, scorecards, promotion/rollback
  receipts, execution telemetry, resource plans, TaskOrientation, imported workloads. Avoids customer
  payloads by default (prefer `payload_ref` / hash / tenant-scoped encrypted payload).
- **Baltor stores:** source artifacts, context objects, atomic facts, held-out allegations, reconciliation
  decisions, verification receipts, context responses, native sidecars, customer data, tenant policy,
  **canonical facts**. The sensitive store.
- **OpenHarnessHub stores:** public skills/templates/harnesses/rubrics/evals/packs + the spec. No private
  customer data.
- **HoldCo stores:** brand/research/portfolio/IP/investor docs only. No runtime customer data.
- **Law (proven):** the sensitive truth types (`canonical_fact`, `context_response_served_facts`,
  `reconciliation_decision`, `customer_context_truth`, `customer_data`) are owned by **Baltor alone** and are
  in every other company's `forbidden_data_types`. Teleon returns **evidence / candidate / result**; it never
  owns or writes Baltor truth.

## Integration contracts (the only coupling)
- **Baltor → Teleon:** run PurposeTask · run side-by-side · get scorecard · get task health · request candidate
  generation · request rollback (via `PurposeTaskProviderPort`; adapters: `teleon_embedded_local`,
  `teleon_local_http`, `teleon_saas_candidate`).
- **Teleon → Baltor:** returns `TaskRun` / `ExecutionResult` / `EvidenceBundle` / `RuntimeDecision` /
  `Scorecard` / `PromotionDecision` / `ResourceReceipt`. **Never** `CanonicalFact` /
  `ContextResponse.served_facts` / `ReconciliationDecision` — Baltor owns those.
- **OpenHarnessHub → Teleon/Baltor:** supplies `SkillManifest` / `HarnessManifest` / `TemplateManifest` /
  `EvalPack` / `CapabilityPack` / `ProviderPack` — **candidate until eval/redteam** (discovery ≠ trust).

## Repo evolution (don't rush the split)
1. **Phase 1 (now):** monorepo with hard boundaries — `src/teleon/`, `src/baltor/`, `src/openharnesshub/` +
   the enforced import law. (The generic runtime is mid-extraction `src/baltor/` → `src/teleon/`.)
2. **Phase 2:** separate packages, same repo — a `shared-contracts` package with **no business logic**;
   `teleon-runtime` imports `shared-contracts`; `baltor-core` imports `shared-contracts` + `teleon-sdk` only.
3. **Phase 3:** separate repos / orgs once API contracts stabilize.

## Local development (planned: `scripts/run_portfolio_local.sh`)
Ports (from `company_portfolio_map.json`): Portfolio hub `:9000` · **Teleon API `:9400`** / web `:9401` ·
**Baltor API `:9307`** (the running admin server) / static `:8000` · **OpenHarnessHub `:9500`**. Discovery via
`TELEON_API_URL` / `BALTOR_API_URL` / `OHH_REGISTRY_URL`. No service requires paid cloud; each runs offline.

## Status / queued
Done + proven: the boundary model + import law + brand-risk register (flywheel 322). **Queued** (full spec
captured in `prompts/contextiseverything-portfolio-infrastructure-split.md`): `run_portfolio_local.sh`, the
`PurposeTaskProviderPort` + Teleon adapters, the website dirs, service-auth implementation, and the remaining
boundary proofs. Brand: run formal trademark/domain clearance on **AI Done Right** and defensive domains before
heavy public use — see the risk register.
