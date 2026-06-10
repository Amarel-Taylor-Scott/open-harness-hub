# Claude Design Handoff — pages, routes, marketing copy, and design needs

_Snapshot: 2026-06-07. A self-contained brief for designing the portfolio surfaces with the **Claude Design**
branded-house system. Every page/route, the governed marketing copy, the design tokens, and the open design work are
here. **Nothing in this doc is invented** — the marketing copy is pulled verbatim from `scripts/portfolio_lib.py`
(`SITES`), the visual system from `docs/design/openharness-claude-design/`, and the full surface enumeration from
`docs/portfolio-web-surface-inventory.md`. Use those as the source of truth; this doc assembles them for handoff._

## 0. How to use this

- **Copy is governed — use it verbatim.** Each site below lists its canonical `one_liner`, `problem`, CTAs, and
  `required_phrases`. The required phrases are enforced (the portfolio proofs fail if a site drops them). Do not
  rewrite positioning; you may design *around* it.
- **Tokens, not hex.** The design system is in `docs/design/openharness-claude-design/shared/` (`oh-tokens.css`,
  `oh-components.css`, `oh-site.css`, `oh-hub.css`). All color/space/radius come from CSS variables; **never hardcode
  a hex in a stylesheet.** Only `--accent` differs per brand.
- **Branded-house, not separate brands.** Same type system, same primitives, same scale across all surfaces — only
  the accent (and a couple of font pairings) changes. Hanken Grotesk (display) + IBM Plex Mono (mono) for Baltor (dir-d).
- **Governance the design must respect:** dashboards are **projection-only** (they display, never assert truth); any
  model output shown is labelled **candidate, never served truth**; **no raw API keys** in any mockup/screenshot (show
  `has_secret_ref` / "key: ref" only); `candidate ≠ active` (label candidate providers/benchmarks as such).

## 1. Brand accents (the one thing that differs per brand)

| Surface | Accent | Type pairing | Role |
|---------|--------|--------------|------|
| ContextIsEverything (HoldCo) | `#2563eb` blue | Hanken Grotesk + IBM Plex Mono | parent / portfolio |
| Teleon | `#6d5ef0` indigo | Hanken Grotesk + IBM Plex Mono | runtime SaaS |
| **Baltor** | `#0e7c86` teal (dark `#2dd4bf`) — coupled to `--verified` | **Hanken Grotesk + IBM Plex Mono (dir-d)** | governed-context product |
| OpenContextHub | `#2f8f6b` green | branded-house | context registry |
| OpenSkillsHub | `#2f7d8f` teal-blue | branded-house | skill graph |
| OpenToolsHub | `#8f6f2f` bronze | branded-house | tool graph |
| OpenHarnessHub | `#d2542f` ember | Hanken Grotesk + JetBrains Mono (dir-s) | harness ecosystem |

(9 brand "directions" × light/dark exist in `oh-tokens.css`; the above are the in-use ones. Full token scale —
`--fs-*`, `--pad-*`, `--r-*`, semantic colors — in `oh-tokens.css`.)

## 2. Portfolio one-pagers (7 sites) — copy + pages + status

Each is a single marketing page (`websites/<id>/` → `dist/sites/<id>/index.html`) with anchored sections:
`hero · what-it-is/owns · what-it-is-not · who-for · governance/core · types/contents · how-it-fits`. **Copy is
canonical from `portfolio_lib.SITES`.** Status: all BUILT (need design polish to the Claude Design system).

### ContextIsEverything Group — accent `#2563eb`
- **one-liner:** "Infrastructure for governed, self-improving AI systems."
- **problem:** "Governed, self-improving AI needs more than one product — it needs a coordinated runtime, a
  governed-context layer, and an open ecosystem, kept distinct yet aligned."
- **primary CTA:** "Explore the portfolio" → `#portfolio` · sections: hero · what-it-is/owns · thesis · companies · how-it-fits.

### Teleon (`teleon.dev`) — accent `#6d5ef0`
- **one-liner:** "Teleon turns functions, jobs, workers, and automations into self-adaptive capabilities."
- **problem:** "Cloud work is provisioned by implementation type (functions, jobs, workers), not by purpose — so it
  can't evaluate a better/cheaper implementation or move runtimes safely on evidence."
- **primary CTA:** "Define your first CapabilityTask" → `#capabilitytask` · sections: hero · owns · core design · runtime adapters · dashboards · how-it-fits.

### Baltor (`baltor.ai`) — accent `#0e7c86` teal
- **one-liner:** "Baltor turns messy, stale, conflicting, and unstructured context into safe, reconciled,
  source-grounded AI context."
- **problem:** "Agents fail on bad context — stale, conflicting, ungrounded — and have no receipt for what they were given."
- **primary CTA:** "Run the CFPB guided demo" → `#cfpb-demo` · narrative tagline (memory): *"Models don't fail. Their context does."*

### OpenContextHub — accent `#2f8f6b`
- **one-liner:** "Open context artifacts for AI systems." · **CTA:** "Browse the context registry".
- **problem:** "Reusable context is scattered and ungoverned — no open registry of source-grounded context packs,
  schemas, and source-handle maps with clear provenance and visibility."

### OpenSkillsHub — accent `#2f7d8f`
- **one-liner:** "The searchable skill graph for AI agents." · **CTA:** "Browse the skill graph".
- **problem:** "Agent know-how is scattered across repos with no searchable, deduped, provenance-tracked graph."

### OpenToolsHub — accent `#8f6f2f`
- **one-liner:** "The executable tool graph for AI agents." · **CTA:** "Browse the tool graph".
- **problem:** "Executable capabilities are scattered and ungated — no open graph with visibility, gating, and sandbox metadata."

### OpenHarnessHub — accent `#d2542f`
- **one-liner:** "Open harnesses, rubrics, templates, and evals for agentic infrastructure." · **CTA:** "Browse the harness ecosystem".
- **problem:** "There is no neutral, reusable place to PROVE that context, skills, and tools actually work."
- **required phrases (verbatim):** "Discovery is not trust." · "OpenHarnessHub.io replaces OpenHarnessHub.org".

## 3. Baltor app (`web/baltor/`) — SPA + feature pages

**SPA routes (marketing funnel)** — apply the dir-d teal Claude Design system:
| Route | Purpose |
|-------|---------|
| `/` (Overview) | three-tier serving model + Context Engine hero + feature surfaces |
| `/engine` | full-screen animated Context Engine (6 macro stages + verification rail) |
| `/pricing` | Assessment (free) · Processing (metered) · Serving packages · Monitored context |
| `/trust` | fact-state lineage · multi-source adoption · reconciliation · provenance |

**The six macro stages** (canonical language single-sourced in `web/baltor/stages.json` — use verbatim on the hero
+ stage pages): **Source Systems → Reconciliation → Anti-Fragility → Enhancement → Optimization → Consumption**, under
a **Verification rail**. (Raw document processing is a BACKEND layer under Source Systems — never a 7th front-end column.)

**Feature / ops pages (live):** `dashboard.html` (Live Ops — 7-stage board + event stream + metrics) · `demo-console.html`
(guided CFPB replay) · `reviews.html` · `hub.html` · `raw.html` · `dev-dashboard.html` · `fleet.html` · `/inference-plane`
(Shared LLM Plane, projection-only). **Explainers (static):** `how-it-works.html` · `context-engine-hero.html` ·
`cfpb-artifact-graph.html` · `temporal-graph.html`. **Stage deep-dives:** `stages/{source,reconciliation,anti-fragility,
enhancement,optimization,consumption}.html`. **Pipeline journey:** `pipeline/{index,upload,decomposition,reconciliation,
verification,enhancement,optimization,consumption}.html`. **Projection pages:** `memory.html` · `native.html` ·
`determinism.html` · `standards.html` · `consume.html`. (Full per-page purpose + status: `docs/portfolio-web-surface-inventory.md`.)

## 4. OpenHarnessHub app (`web/harness-hub/`) — needs the most design

Landing (`/`) + logged-out build preview (`#/preview`) are LIVE. **~24 routes are TEMPLATE (styled, JS pending) —
these are the priority design surfaces:** explore (`/pipelines`, `/components`, `/c/:slug`), build/flow/run, foundry
(`/workers`, `/byo`), govern (`/freshness`, `/attest`, `/trust`, `/audit-log`), connect (`/improve`, `/connect`,
`/sources`), admin (`/admin`, `/checkout`), `/solutions`, `/value`, `/why`, `/docs`, `/compare`, `/deep`. Accent dir-s ember.

## 5. UI primitives the designer works with

The component kit (in `docs/design/openharness-claude-design/shared/oh-components.css` + `oh-explorations.css`):
buttons (`.oh-btn`), cards (`.oh-card`), badges/pills (`.oh-badge` — lift/verified/warn/danger), headings/eyebrow,
tabs, segmented control, form fields, switch, table, meter/progress, stat tiles, nav/wordmark/topbar, sidebar,
page/shell/split layout, marketing hero + entry box + chips, command palette, drawer, **component card**, **flow
canvas/DAG nodes** (colored by the 7 product primitives), vertical/subway/trace/batch diagrams, lift-evidence panel,
result/recommendation card, budget/quality dial, scheme switcher, state messaging (blocked/empty/toast), pricing
tiers, account/settings/facets. (Full list with files: `docs/portfolio-web-surface-inventory.md` §13A.)

**Product-primitive legend colors** (shared across brands, in tokens): Input (grey) · Knowledge Corpus (green) ·
If Statement (gold) · Action (red) · Loop (purple) · Stop/End (red) · Output (blue).

## 6. Open design work (what to design, by priority)

1. **OpenHarnessHub app — the ~24 templated routes** (§4): the biggest concrete design surface; CSS scaffolding exists.
2. **Account / authenticated surfaces** (across products): auth · billing (per-project, not connected) · usage ·
   settings · dashboard. Brief: `prompts/portfolio-app-console-build-brief.md`.
3. **Design-system migration:** `web/baltor/dashboard.html` + `native.html` use **ad-hoc inline hex** instead of the
   `oh-*` tokens — migrate them onto `.oh.dir-d.theme-dark` (needs visual before/after verification).
4. **Polish the 7 one-pagers** to the Claude Design system (currently functional, not fully on the kit).
5. **A `COMPONENTS.md`** in `docs/design/openharness-claude-design/` — per-component states/nesting/examples (the
   tokens are documented; the components aren't, line by line).

## 7. HELD — needs owner decision before design (do NOT mock as shipping)

- **OpenMCPHub / OpenCompressionHub / OpenBenchmarkHub sites** — named hubs with NO site; building them asserts **new
  public `.io` domains** that need domain/trademark clearance. Design only after the owner clears the domains.
- **Teleon Control Tower (staff) + Capability Assurance Portal (customer)** — the runtime's authenticated UI is
  greenfield (separate TS build, `prompts/teleon-build-kit.md`). Largest net-new design opportunity; owner-scoped.

## 8. Canonical sources (don't duplicate — pull from these)

- Marketing copy (one-liners, problems, CTAs, required phrases, accents): `scripts/portfolio_lib.py` → `SITES`.
- Visual system + tokens + existing handoff: `docs/design/openharness-claude-design/` (`FAMILY-README.md`,
  `HANDOFF.md`, `MARKETING.md`, `shared/oh-tokens.css`, `shared/oh-components.css`).
- Full page/view/route/primitive enumeration with status + gaps: `docs/portfolio-web-surface-inventory.md`.
- Baltor stage language (single source): `web/baltor/stages.json`.
- Brand law (only `--accent` differs; never hardcode hex) enforced by `scripts/check_baltor_design_system.py`.
