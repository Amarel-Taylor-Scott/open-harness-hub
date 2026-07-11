# Portfolio architecture — Teleon · Baltor · OpenHubForAI registries (under AI Done Right)

**Status:** OWNER-DECIDED 2026-06-06. This is the canonical brand + dependency architecture. It supersedes the
single-company framing in [brand-architecture-and-naming] and the "Purpose Runtime as a Baltor subsystem"
framing. The dependency law below is enforced by `scripts/check_portfolio_dependency_law.py` over
`architecture/portfolio_dependency_law.json` (single source) — not by prose.

## The portfolio

```
AI Done Right    (umbrella IP · brands · standards strategy · shared R&D/security/governance · cap table)
├── Teleon.dev      — ITS OWN product + the runtime: program capabilities in PLAIN TEXT -> auto-adapt to the cheapest-BOUNDED form within your guardrails (governs EFFICIENCY)
├── Baltor.ai       — ITS OWN product: fully MANAGED company-/department-/initiative-wide governed context, powered by Teleon (a TENANT) (governs TRUTH)
└── OpenHubForAI registries       — the open registry Teleon, Baltor, and AIDevObserver consume: primitives · templates · context · tools · models · steps · DAG components · reconciliation/robustness/enrichment rules · modules (run on Teleon or custom compute) · skills · harnesses · evals · specs
```

**Moat split (LOCKED 2026-06-21):** Baltor governs what becomes **TRUE**; Teleon governs what becomes **EFFICIENT**
(the descent brain). Both "govern" — different objects, never the same. **Two standalone products**, distinct buyers:
Baltor = orgs that want managed context; Teleon = people who want to program capabilities in plain text.

The biggest change from before: **PurposeTask is no longer a Baltor subsystem.** It is **Teleon**. Baltor
becomes the first internal customer (tenant `baltor-internal`). This keeps the runtime independently valuable
and gives OpenHubForAI a natural role as the open standard/evidence ecosystem.

## Each brand

### Teleon (`teleon.dev`, domain owned) — the runtime
The purpose-driven, eval-gated, self-adaptive compute runtime SaaS. **Owns:** PurposeTask/CapabilityTask
registry · runtime selection · implementation candidates · evidence ledger · promotion gates · policy gates ·
boundary approvals · task orientation · self-adaptation loop · runtime adapters · staff/customer assurance
dashboard. **Category:** purpose-driven runtime / eval-gated self-adaptive compute / capability-oriented cloud
runtime. **One-liner:** *Serverless runs code. Kubernetes runs workloads. Teleon runs purpose.* Reusable by
Baltor but **not limited to Baltor**.

### Baltor (`baltor.ai`) — the applied product
The customer-facing intelligence system that uses Teleon underneath. **Owns:** customer workflows ·
domain-specific outcomes · source/evidence UX · receipts · customer workspaces · vertical integrations ·
Baltor-specific agents/task catalogs/business logic. **No longer owns directly:** the generic adaptive worker
runtime, PurposeTask infrastructure, runtime switching, the promotion/eval control plane, or generic task
dashboard primitives — those are Teleon's. **Story:** *Baltor is powered by Teleon.*

### The OpenHubForAI family (split 2026-06-06; expanded design family 2026-06-09)
The open ecosystem is a focused hub family, not one junk drawer (bridge graph:
`architecture/open_hubs_bridge_graph.json`; **none is a truth authority**):
- **OpenContextHub.io** — reference context artifacts · context packs · schemas · source-handle maps ·
  decomposition maps · native sidecars · fixtures. *Reference context is not served truth — Baltor governs it.*
- **OpenSkillsHub.io** — the open **skill graph**: skills · playbooks · workflows · SKILL.md packages · agent instructions.
- **OpenToolsHub.io** — the open **tool graph**: executable tools · MCP servers · APIs · CLIs · adapters · workers.
- **OpenHubForAI.io** — the **proof** layer: harnesses · rubrics · eval packs · fixtures · templates · datasets ·
  conformance packs. **OpenHubForAI.io replaces OpenHubForAI.org** as the preferred public site.
- **Additional live/private-first registry surfaces** — OpenSkillToTool, OpenMCPHub, OpenCompressionHub,
  OpenBenchmarkHub, OpenReviewHub, the private bench, and the Baltor method spine are captured in the
  AI Done Right design handoff. They remain registry/discovery surfaces; discovery is not trust.
  - **Method-hub boundary (LOCKED 2026-06-21):** the 5 Baltor method-hubs (Open{Reconciliation,Hardening,Enrichment,
    Optimization,Verification}Hub) are STORE components — they register **method SPECS only** (candidate; discovery≠trust).
    **Baltor SELECTS a method (via Teleon) -> RUNS it on customer data -> OWNS the resulting truth.** The spec lives in the
    store; execution + governed truth live in Baltor (no duplicated implementation). Baltor's moat is the governed DATA +
    receipts, not the technique — so publishing specs leaks no moat.

**Relationship:** OpenContextHub supplies context → OpenSkillsHub teaches how → OpenToolsHub gives execution →
OpenHubForAI proves it works → Teleon runs/evolves capabilities → Baltor governs context + decides truth →
AI Done Right coordinates. *Teleon implements the open CapabilityTask Spec* (stewarded across the open hubs)
— not a proprietary YAML.

### Holding company — **AI Done Right**
Owns the umbrella IP/brands/standards-strategy/corporate structure; sponsors OpenHubForAI. Not prominent to
customers at first — the legal/strategic parent. **Owns no runtime code and no customer data** (enforced by
`check_company_portfolio_boundaries.py`). Current displayed parent brand is **AI Done Right**
(`aidoneright.dev`); the code slug `contextiseverything` remains as a stable identifier. Formal trademark/domain
clearance remains owner-gated before heavy public use (see `architecture/domain_brand_risk_register.json`).
Full infra topology + boundaries:
[infrastructure-topology](../portfolio/infrastructure-topology.md).

## The dependency law (architectural law — enforced)

```
Baltor ──────────────► Teleon ──────────────► OpenHubForAI
(applied product)      (runtime SaaS)         (open ecosystem + spec)
```

- **Baltor depends on Teleon** (calls the Teleon API as tenant `baltor-internal`).
- **Teleon may consume OpenHubForAI** artifacts (harnesses, templates, skills, the spec).
- **OpenHubForAI depends on neither.**
- **FORBIDDEN:** Teleon importing Baltor · OpenHubForAI importing Baltor or Teleon · Baltor owning generic
  Teleon concepts. (`check_portfolio_dependency_law.py` fails the build on any forbidden import edge.)

## Vocabulary (standardize across all three)
**PurposeTask** (stable purpose-level contract; product language) · **CapabilityTask** (the formal/spec name,
stewarded by OpenHubForAI) · **ImplementationCandidate** (a means under test) · **RuntimeBinding** (where it
runs) · **EvidenceLedger** (runs/evals/traces/receipts/scorecards/cost/latency/safety) · **PromotionGate**
(evidence+policy decision) · **BoundaryApproval** (human approval for an ends change) · **TaskOrientation**
(operational memory) · **AssurancePortal** (staff/customer trust visibility). Staff dashboard = **Teleon Control
Tower**; customer dashboard = **Capability Assurance Portal**.

## What moves out of Baltor → Teleon (incremental, lossless — never big-bang)
Generic concepts move to Teleon; Baltor keeps only Baltor-specific task definitions + vertical logic. Tracked
in `architecture/portfolio_dependency_law.json` → `migration_status`. Extraction order:
1. **Execution layer** — `_repos/baltor/backend/src/baltor/workers/{execution_backend_selector,execution_dispatch,execution_providers/*}` → `_repos/teleon/backend/src/teleon/runtime` (lowest layer; extract first).
2. **Parallel-Path Engine** — `_repos/baltor/backend/src/baltor/experiments/*` → `_repos/teleon/backend/src/teleon/experiments` (side-by-side + promotion).
3. **PurposeTask** — `_repos/baltor/backend/src/baltor/purpose_tasks/*` → `_repos/teleon/backend/src/teleon/purpose_tasks` (controller + CTS-1 binding + adaptation ladder + projections).
4. Add `_repos/baltor/backend/src/baltor/teleon_client` so Baltor calls the Teleon surface as a tenant.

Each step: move a layer + update its imports + its proofs, re-run the flywheel GREEN, keep the raw/lineage
(lossless). The dependency-law proof guards every step against a backward import.

## Teleon API surface (the boundary Baltor calls)
```
POST /purpose-tasks                          GET  /purpose-tasks            GET /purpose-tasks/{id}
POST /purpose-tasks/{id}/run                 POST /purpose-tasks/{id}/evaluate
POST /purpose-tasks/{id}/run-side-by-side    POST /purpose-tasks/{id}/promote
POST /purpose-tasks/{id}/rollback            POST /purpose-tasks/{id}/request-boundary-approval
GET  /purpose-tasks/{id}/evidence            GET  /purpose-tasks/{id}/customer-assurance
```
`promote` opens a Promotion + runs the policy engine; it never deploys directly. (Full data model + redteam +
phased plan for Teleon's control & trust plane: `prompts/teleon-build-kit.md` — a separate greenfield build.)

## Cloud hosting topology — co-located, cleanly separable (owner-directed 2026-06-06)

**Goal:** Teleon.dev and Baltor.ai sit *close* (Baltor is a high-frequency caller of Teleon, so the hop must be
cheap) yet stay *separable* (either can be spun out, sold, or moved without code surgery).

**Co-location for latency**
- Deploy both in the **same cloud region** and **same private network** (one VPC, or peered VPCs / private
  service connect). Baltor→Teleon calls travel the **private network** (single-digit-ms intra-region), never
  the public internet.
- Optionally co-resident in one cluster with a **service mesh**; public traffic still enters via the two
  separate domains (`baltor.ai`, `teleon.dev`).

**Separation so a clean split stays cheap (the levers)**
1. **Stable, versioned API contract** between them (the Teleon API above) — the only coupling.
2. **No shared database.** Teleon owns its runtime/evidence store; Baltor owns customer data. No cross-DB
   joins; integrate via the API + events, not a shared schema.
3. **No shared code except via the open spec / published packages** (OpenHubForAI artifacts + the CapabilityTask
   spec) — never a private import across the boundary (enforced by the dependency-law proof).
4. **Separate identity/billing/IaC:** separate cloud projects/accounts (or at least separate namespaces + IAM
   + billing tags), separate infrastructure-as-code stacks, so either redeploys independently.
5. **Failure isolation / graceful degrade:** if Teleon is unreachable, Baltor degrades to a local fallback
   (the same *cloud-defer-only-after-local-equivalent* discipline already in the runtime) behind a circuit
   breaker — Baltor never hard-fails because Teleon is down.

**Net:** one region + one private network = low latency today; separate service + data + identity + IaC + a
versioned contract = a clean cut tomorrow. This is the same flexibility principle as
[execution-backend-flexibility] applied at the company-topology level. (Concrete IaC scaffolds —
same-region/peered-VPC, private service-to-service auth, per-service stacks — are a later deliverable; this doc
sets the constraint.)

## Related
[teleon-naming-and-domain] · [cloud-task-self-adapting-execution] (PurposeTask = Teleon's core object) ·
[execution-backend-flexibility] · [name-and-open-core-model] · build kit `prompts/teleon-build-kit.md`.
