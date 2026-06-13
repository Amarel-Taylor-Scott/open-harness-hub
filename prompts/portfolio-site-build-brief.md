# Portfolio Website Build Brief — page architecture for the 7 sites

A build brief for Claude Code to turn the current **one-pagers** into proper **multi-page sites**. Seven sites,
one shared design system, strict brand boundaries. Source of truth for copy/ports/accents/boundary rules:
`scripts/portfolio_lib.py` (SITES / SIGNATURE / required_phrases / forbidden_identity). Portfolio thesis:
`docs/strategy/teleon-baltor-openharnesshub-portfolio.md`.

## Current state (do not regress)
- Each site is a single `dist/sites/<id>/index.html` with anchor sections (`#thesis`, `#capabilitytask`, …),
  rendered by `portfolio_lib.render_site` / `render_hub`. Ports: hub 9100; sites 9101–9107.
- **Brand-boundary law (enforced by `check_portfolio_*` proofs):** every page carries delimited
  `<!--IDENTITY-->` and `<!--RELATIONSHIP-->` zones. A site's IDENTITY zone MUST contain its `required_phrases`
  and MUST NOT contain any other brand's `forbidden_identity` signature claim. Cross-links/relationship mentions
  are allowed only in the RELATIONSHIP zone. Some sites also have `forbidden_anywhere` phrases.
- No external CDN/JS/fonts/analytics/secrets. System-font stack, embedded CSS, dark theme, per-site accent.
  Pages are projection-only (store no data, write no truth).
- **If you go multi-page, keep these guarantees** — extend `portfolio_lib.py` (still single-source) or replace
  the renderer, but update the `check_portfolio_*` proofs in the SAME change so required_phrases/boundaries
  still hold per page. Keep the dependency-law cross-links: `OpenHarnessHub → Teleon → Baltor`,
  AI Done Right coordinates.

## Shared system (build once, reuse on all 7)
- **Component library:** sticky header (brand dot + name + `kind` tag + nav), hero (pill + h1 + lead + dual CTA),
  section blocks, "what it is / what it is NOT" two-column, owns/not-owns table, dependency diagram, footer with
  cross-links + `LOCAL_DEMO_DISCLAIMER`.
- **Accents (per-site `--accent`):** AI Done Right `#5b6cff` · Teleon `#21c7a8` · Baltor `#ff8a3d` ·
  OpenContextHub `#3da9fc` · OpenSkillsHub `#c77dff` · OpenToolsHub `#f6c945` · OpenHarnessHub `#21d3a0`.
- **Global pages every site gets:** `/` `/about` `/legal/privacy` `/legal/terms` `/contact` + a 404. Product
  sites (Teleon, Baltor) also get `/security`, `/pricing`, `/docs`, `/blog`, and app entry `/login` `/signup`.
  Hubs share one registry template (below).
- **Design direction:** acquired-AI-infra-tool grade (clean, confident, lots of whitespace, real diagrams) —
  NOT generic dev-dark-plus-orange. Give Claude Code design best-practices + 2–3 layout options per key page;
  don't pre-pick.

---

## 1. AI Done Right (founding thesis: ContextIsEverything) — holding company / investor site (`#5b6cff`)
One-liner (IDENTITY): **"Infrastructure for governed, self-improving AI systems."** Audience: founders,
investors, partners, researchers. It owns NO runtime/product — pages must reflect that.

| Route | Page | Purpose / key sections | Primary CTA |
|---|---|---|---|
| `/` | Home | Portfolio thesis in one screen; the 3 companies; dependency diagram `OpenHarnessHub → Teleon → Baltor`; "what we do NOT own" | Explore the portfolio |
| `/portfolio` | Portfolio | Cards for Teleon, Baltor, OpenHarnessHub (+ the 3 other hubs) → link out to each site; one-line each + owns/not-owns | Visit each company |
| `/thesis` | Portfolio thesis | The essay: a model is only as good as its context + runtime; why 3 focused companies | Read the architecture |
| `/architecture` | How they fit | The dependency law (Baltor→Teleon→hubs, never reverse); who owns what / who never owns truth; boundary diagram | — |
| `/standards` | Open standards | Coordination of CTS / CapabilityTask spec, OIPS, shared schemas; where each spec lives | See OpenHarnessHub |
| `/research` | Research | Index of shared research notes/publications | — |
| `/about` | About | Mission, structure, (team), holding-company model | — |
| `/investors` | Investors | Thesis-for-investors, traction (demos/proof), contact | Request the deck |
| `/contact` `/legal/*` | Contact + legal | Inquiries; privacy/terms | — |

Boundary: NOT a product you deploy · NOT a runtime · NOT an owner of context truth or skill activation.

---

## 2. Teleon — product SaaS site, `teleon.dev` (`#21c7a8`)
One-liner: **"Teleon turns functions, jobs, workers, and automations into self-adaptive capabilities."**
Category: *intent-native, eval-gated, self-adaptive compute*. Audience: platform-eng, AI-infra, DevOps/SRE,
automation. **Forbidden anywhere:** "deploy agents in minutes", "Vercel for agents", "deploy AI agents in minutes".

| Route | Page | Purpose / key sections | Primary CTA |
|---|---|---|---|
| `/` | Home | Hero + the loop `purpose → contract → runtime selection → candidate → evidence → eval-gated promotion/rollback` | Define your first CapabilityTask |
| `/platform` | How it works | The runtime: runtime selection, evidence ledger, promotion/policy gates, boundary approvals | See the CapabilityTask |
| `/capabilitytask` | The core object | The five-line law: *CapabilityTask stays stable. Implementation evolves. Runtime changes. Evidence decides. Policy gates promotion. Humans approve boundary expansion.* + PurposeTask vs CapabilityTask | — |
| `/runtimes` | Runtime adapters | local function · managed venv · local job · worker pool · cloud function · K8s job · queue worker · browser worker · GPU worker; switchable on evidence | — |
| `/lift` | Teleon Lift | Import existing cloud functions / K8s → ImportedWorkload → PurposeTaskDraft; read-only-first adoption ladder; legacy = rollback baseline | Import a workload |
| `/evidence` | Evidence & eval-gating | Measured-lift, side-by-side candidate runs, the evidence ledger, promotion gates | — |
| `/dashboards` | Dashboards | **Teleon Control Tower** (staff) + **Capability Assurance Portal** (customer): one truth model, two governed views (dashboard never owns truth) | — |
| `/use-cases` | Use cases | Govern automations, modernize cloud functions safely, multi-runtime portability | — |
| `/security` | Security/trust | Boundary approvals, secret handling (refs only), isolation, Teleon↔Baltor separability | — |
| `/pricing` | Pricing | SaaS tiers | Start free / Book a demo |
| `/docs` | Docs | Quickstart, SDK, CapabilityTask spec, API, runtime adapters | — |
| `/blog` `/changelog` | Updates | — | — |
| `/login` `/signup` `/contact` `/legal/*` | App + legal | — | — |

Boundary: NOT a generic AI-agent deploy product · NOT a K8s replacement · NOT a cloud-functions replacement ·
NOT unbounded self-modifying code.

---

## 3. Baltor — applied product site, `baltor.ai` (`#ff8a3d`)
One-liner: **"Baltor turns messy, stale, conflicting, and unstructured context into safe, reconciled,
source-grounded AI context."** Narrative line: *"Models don't fail. Their context does."* Pillars: **Verify ·
Corpus · Compress**. Audience: regulated-AI, compliance, risk, legal-ops, enterprise-copilot.

| Route | Page | Purpose / key sections | Primary CTA |
|---|---|---|---|
| `/` | Home | "Models don't fail. Their context does."; the problem (bad context, no receipt); the pipeline at a glance | Run the CFPB guided demo |
| `/context-engine` | The Context Engine | Six-stage pipeline: `Intake → Decomposition → Atomic facts → Conflict detection → Reconciliation → Fragility/freshness → Optimization → Consumption → Receipts` + the universal verification rail | — |
| `/how-it-works` | Verify · Corpus · Compress | The three pillars in depth | — |
| `/demo` | CFPB guided demo | Serves Reg E "10 business days," holds out FAQ "30 days," preserves receipts/source handles; link to the live console | Open the live demo |
| `/solutions` | Solutions | By use case: sanctions/compliance (beachhead), financial services, legal ops, enterprise copilots | — |
| `/trust` | Receipts & verification | Portable receipt, provenance, source handles, continuous verification, freshness/CDC; "AI drafts, humans sign off" | — |
| `/built-on-teleon` | Powered by Teleon | Baltor is a Teleon tenant via `PurposeTaskProviderPort`; Teleon returns evidence/candidate/result, Baltor decides served truth | — |
| `/security` `/compliance` | Security & compliance | Data handling, separability, governance posture | — |
| `/pricing` | Pricing | Tiers (free exports funnel → governed/live layer → build-on-demand) | Book a demo |
| `/docs` `/resources` `/blog` | Docs + resources | — | — |
| `/login` `/contact` `/legal/*` | App + legal | — | — |

Boundary: NOT a generic compute runtime (that's Teleon) · NOT a generic cloud-task orchestrator · NOT an open
skill registry (that's OpenHarnessHub).

---

## 4–7. The four open hubs — one shared registry template, four instances
All four are OSS-first **registry** sites with the same shape; only the entity, facets, accent, and signature
copy differ. Shared governance line on every hub: **"Discovery is not trust."** (+ reference/sandbox/candidate
≠ truth). Each hub's `/about` states the portfolio relationship (consumed by Teleon, governed by Baltor).

**Shared hub page template:**

| Route | Page | Purpose |
|---|---|---|
| `/` | Home | One-liner + governance rule + "Browse the X" CTA + how it feeds the portfolio |
| `/browse` (a.k.a. `/registry`) | Catalog | Searchable, filterable list with facets; status badges (candidate/active/quarantined) |
| `/<entity>/:id` | Detail | One artifact: provenance, source, visibility, status, alternatives/fallbacks, sandbox/eval status |
| `/spec` (`/schema`) | Contracts | The artifact types + JSON schemas |
| `/governance` | Governance & visibility | The core rule + visibility tiers + promotion ladder |
| `/contribute` | Publish | How to publish; provenance + license requirements; "discovery ≠ trust" gate |
| `/docs` `/about` `/legal/*` | Docs + relationship + legal | Where it sits in the portfolio |

Per-hub specifics:

- **OpenContextHub** (`#3da9fc`) — *"Open context artifacts for AI systems."* Entities: ContextArtifact ·
  SourceArtifact · ContextPack · ContextManifest · SourceHandleMap · DecompositionMap · ContextSchema ·
  NativeSidecar · ContextFixture. `/governance` headline: **"Reference context is not served truth. Baltor
  governs context before consumption."** Visibility tiers: PUBLIC_REFERENCE · PUBLIC_METADATA ·
  GATED_CONTEXT_PACK · CUSTOMER_PRIVATE · INTERNAL_ONLY · QUARANTINED.

- **OpenSkillsHub** (`#c77dff`) — *"The searchable skill graph for AI agents."* Entities: skills · playbooks ·
  workflows · SKILL.md packages (provenance + dedup). Detail page shows alternatives/fallbacks + sandbox/eval
  status. Relationship: skills USE OpenToolsHub tools, are PROVEN by OpenHarnessHub, draw context from
  OpenContextHub, run via Teleon. Governance: "A skill is instructions, not execution; skill output is not truth."

- **OpenToolsHub** (`#f6c945`) — *"The executable tool graph for AI agents."* Entities: MCP servers · APIs ·
  CLIs · adapters · workers — each with visibility/gating + sandbox metadata. This hub also surfaces the
  **free/limited LLM endpoint intelligence** metadata (provider risk + class) and browser-runtime candidates
  (e.g. ClawLess) — all `executable: false`, gated through Teleon's Inference Gateway. Governance: "A tool is
  gated and sandboxed before use; tool output is not truth."

- **OpenHarnessHub** (`#21d3a0`) — *"Open harnesses, rubrics, templates, and evals for agentic
  infrastructure."* Entities: harnesses · rubrics · eval packs · fixtures · templates · datasets · conformance
  packs. ALSO the home of the **open CapabilityTask spec (CTS)** — give it a prominent `/cts` (or `/spec/cts`)
  page. Note: "OpenHarnessHub.io replaces OpenHarnessHub.org as the preferred public site." Governance: "A
  passing eval is evidence, not a guarantee; missing coverage blocks promotion." Forbidden anywhere: "hosted
  runtime we operate", "fully managed SaaS runtime".

---

## Build order suggestion (for Claude Code)
1. Shared component library + design tokens (accents/typography/layout) + the 5 global pages × template.
2. The registry template → instantiate the 4 hubs (highest reuse).
3. Teleon (product depth: platform / capabilitytask / runtimes / lift / dashboards).
4. Baltor (context-engine / demo / trust / built-on-teleon).
5. AI Done Right (thesis / architecture / standards / investors).
6. Re-assert the brand-boundary proofs per page; keep `flywheel --once` green.
