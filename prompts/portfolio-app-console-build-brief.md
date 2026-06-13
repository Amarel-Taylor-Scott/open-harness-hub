# Portfolio App / Console Build Brief — the authenticated (signed-in) surfaces

The "behind the login" architecture for the portfolio. The public marketing sites are specced in
`prompts/portfolio-site-build-brief.md`; THIS brief is the **product** — what users see and manage after they
sign in. The complexity is not page count; it is **identity, tenancy, roles, and governed actions across
multiple products**. Three OPEN decisions (§5) gate the rest.

## What exists today (ground truth, not greenfield-everywhere)
- **Data plane is already multi-tenant:** `tenant_id` flows through `CapabilityTask.v1`, `PurposeTaskSpec.v1`,
  objects, receipts. The Shared I/O Spine (`architecture/shared_io_spine.json`) already gives us ObjectShell,
  CommandEnvelope, EventEnvelope, ResourceRef, ModelInvocationReceipt, work-I/O, etc.
- **Many projection consoles exist but are UNAUTHENTICATED demos:** `web/baltor/{dashboard,reviews,fleet,
  demo-console,consume,integrate,...}.html`, `web/harness-hub/pages/{admin,govern,build,catalog,auth}.js`,
  and the admin server routes (`/admin-demo/*`, `/api/admin-dashboard/*`, `/api/context-gateway/*`).
- **Greenfield (must build):** real identity/auth/session, organizations/workspaces, RBAC, invites, API keys
  (as secret_refs), billing/usage, audit log, the account module. There is no login/session/role system yet.

So the move is: keep the existing consoles as the **projection layer**, and build the **account + identity +
RBAC + governed-action** layer underneath them.

## 1. Why it's complicated (the five cross-cutting concerns — solve these FIRST)

1. **Identity topology** (the biggest fork — §5 Q1). Locked facts: identity is meant to be *separable*
   (`separate service/data/identity/IaC`), and **Baltor is a tenant of Teleon**. So a Baltor customer is, under
   the hood, a Teleon tenant — but should they ever *see* Teleon? Options: one federated portfolio SSO vs
   independent per-product accounts vs hybrid.
2. **Tenancy hierarchy** (§5 Q2). What is the unit of isolation / billing / RBAC scope? `tenant_id` exists at
   the data level; the UI needs an explicit Org → Workspace → Environment (dev/stage/prod) hierarchy mapped onto it.
3. **The staff ↔ customer duality** (LOCKED for Teleon, generalizes to all). Every product has TWO consoles:
   - **Customer console** — manage *your own* tenant (Teleon = *Capability Assurance Portal*; Baltor = customer
     context console; Hubs = contributor console).
   - **Staff / operator console** — manage the *platform across tenants* (Teleon = *Teleon Control Tower*;
     Baltor = ops; Hubs = moderation). Plus a portfolio-level staff command center for the holding co.
   Different auth realm, different RBAC, and **neither console ever owns truth** — both are projections.
4. **Shared account primitives** every signed-in app needs (build ONCE, reuse everywhere): members/roles/invites,
   API keys & secrets (refs only), billing/usage/plan, audit log, notifications, security (SSO/MFA/SCIM), data
   residency, support. This is the "Account & Org" module.
5. **Governed actions, not raw writes** (the safety through-line, from the Shared I/O Spine). In every console a
   user "manages things" by **issuing a governed command** (CommandEnvelope / CapabilityTask), **viewing a
   projection** (ObjectShell / receipts / events), with **secrets as refs**, **approvals as boundary-approval
   objects** (→ HumanApprovalReceipt), and **everything audited**. The dashboard never writes truth.

## 2. Shared console architecture (build once, reuse on every product)

- **Authenticated app shell:** left nav · org/workspace switcher · environment switcher · global search ·
  command palette · notifications/inbox · account menu. Per-product modules slot into this shell.
- **Account & Org module (identical across products):** Overview · Members & roles · Invites · API keys &
  secrets (secret_refs, never raw) · Billing & usage · Plans · Audit log · Security (SSO/MFA/SCIM) · Data
  residency · Notifications · Support/Status.
- **RBAC:** base roles `owner · admin · operator · reviewer · member · viewer` scoped at org/workspace, PLUS
  product-specific permissions — e.g. Baltor **steward** (approves served truth), Teleon **promotion approver**
  / **boundary approver**. Roles map to `schemas/policy/*` (TenantScope/VisibilityPolicy — queued in the spine).
- **Spine objects surface directly:** receipts explorer, evidence ledger, event/audit stream (CloudEvents),
  resource bindings, model-invocation receipts — these are the same contracts the back end already speaks.
- **Design:** acquired-AI-infra-tool grade; dense but calm; one design system, per-product accent (matching the
  marketing sites). Offer 2–3 layouts for the high-traffic screens (overview, the primary object list, detail).

## 3. Per-product authenticated surfaces

### Teleon — the runtime (most complex)
**Capability Assurance Portal (CUSTOMER)**
`/app` Overview (capability health, recent promotions, alerts) · `/capabilities` (CapabilityTask list) ·
`/capabilities/:id` (contract · current implementation · runtime · status · evidence) · `/runs` (run history +
evidence ledger) · `/candidates` (side-by-side candidate vs baseline → request promotion) · `/promotions`
(decisions + rollback) · `/approvals` (pending boundary approvals — human sign-off) · `/policies` (gates,
thresholds) · `/runtimes` (adapters in use) · `/models` (routing preferences + ModelInvocationReceipts: which
model actually ran) · `/sandbox` (sandbox runs) · `/resources` (ResourceRefs/bindings) · `/lift` (import cloud
fn/K8s → drafts) · Account & Org module.
**Teleon Control Tower (STAFF)** — cross-tenant: fleet (workers/supervisor/ledger/DLQ) · all CapabilityTasks ·
promotion-queue oversight · provider graph & model-gateway health · policy templates · tenants · capacity/cost ·
incidents · feature flags · platform audit.

### Baltor — governed context (tenant of Teleon)
**Customer console** — "manage things" = govern context:
`/app` Overview (freshness, open conflicts, served-context health) · `/sources` (connectors + sync state) ·
`/runs` (the six-stage pipeline live: Intake→…→Receipts) · `/objects` (context objects / atomic facts browser) ·
`/conflicts` (contradictions + reconciliation) · `/reviews` (steward review queue — approve / hold / escalate;
this is where humans approve served truth) · `/packs` (context packs + receipts) · `/receipts` (provenance &
receipt explorer) · `/freshness` (rot/CDC monitor) · `/verification` (verification rail dashboard) · `/consume`
(serve endpoints, API keys, playground) · `/demos` (CFPB) · Account & Org module.
**Staff/ops** — tenant oversight · source-adapter health · model/cost · queue/DLQ · the admin-demo monitoring
promoted to real ops.

### The four hubs (OpenContextHub / OpenSkillsHub / OpenToolsHub / OpenHarnessHub) — mostly public; contributors sign in
**Contributor console (shared across all four):** `/app` My artifacts · `/publish` (new — with provenance +
license + sandbox/eval gate; discovery≠trust) · `/drafts` (candidates + promotion status) · `/versions` ·
`/namespace` (org/handle) · API tokens · Profile.
**Maintainer/staff:** moderation/governance queue · quarantine · abuse reports · namespace disputes · registry
health.

### AI Done Right (founding thesis: ContextIsEverything) — holding company
Minimal product surface. Candidates: the **portfolio identity provider** home (if federated SSO) + an internal
**cross-portfolio command center** (read-only health rollup of all products — the Demo Control Tower grown up) +
an investor data room. Not a tenant-facing app.

## 4. Tie to the Shared I/O Spine (why this stays safe at scale)
Every screen is a **projection** of spine objects; every action is a **CommandEnvelope/CapabilityTask**; every
secret is a **SecretRef/KeyRef**; every approval emits a **HumanApprovalReceipt**; the audit log IS the
**CloudEvents** stream; "manage a resource" goes through **ResourceRef/DataResourceSpec**, never a raw console
write. The consoles are thin, governed windows onto the runtime — consistent because they all speak the spine.

## 5. OPEN decisions (owner's call — everything else branches on these)
1. **Identity topology** — federated portfolio SSO vs independent per-product accounts vs hybrid (shared login,
   isolated data/billing). Sub-question: does a Baltor customer ever directly see/log into Teleon?
2. **Tenancy & billing unit** — Org → Workspace → Environment vs Org → Project (flat) vs Workspace-only; and is
   the billed/isolation unit the Org or the Workspace?
3. **App-shell strategy** — one shared multi-product console (single sign-in + product switcher) vs separate
   standalone apps per product (sharing only the design system). Ties to #1 and the separability law.

(These are product-structure decisions; per the change-verification contract they need owner intent, not a
unilateral call. Once chosen, this brief is finalized and handed to Claude Code in build order: account/identity
layer → shared app shell → Teleon portal → Baltor console → hub contributor console → staff/control-tower views.)
