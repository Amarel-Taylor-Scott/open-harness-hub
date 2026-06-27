# START HERE — Claude Code Handoff (AI Done Right)

This repo is the **design + implementation spec** for **AI Done Right** (`aidoneright.dev`),
an AI platform company: 2 governed products (Baltor, Teleon) + a parent portfolio site +
21 open registries — **24 surfaces** on one shared design system. Everything is a
**high-fidelity prototype** (HTML + React-via-in-browser-Babel, mock data). Your job is to
**recreate these designs in a real codebase**, not to ship the HTML.

---

## 1. Paste this into Claude Code to begin

```
You are implementing the "AI Done Right" design portfolio in a production codebase.

The files under openharness/ are FINAL-FIDELITY design prototypes (HTML + React via
in-browser Babel, mock data). They are the spec. Your job is to TRANSPLANT them into a
real toolchain — NOT to redesign, modernize, or reinterpret them. A previous attempt
drifted from the designs; openharness/DESIGN-CONTRACT.md now governs, and it overrides
anything more permissive. Read it FIRST and treat every rule as a failing test.

YOUR FIRST TASK — before any code (DESIGN-CONTRACT Rule 9):
  Read openharness/SYSTEM-INVENTORY.md and print its recognition table, filled in from
  the actual repo: 24 surfaces, 23 PORTFOLIO entities, 21 hubs rendered by ONE makeHub,
  12 private-bench, 39 oh-site.jsx exports, the 6-method A/B engine (define/variant/
  assign/clear/track/exposure + ?exp= forcing + dataLayer), 8 bespoke + 42 per-hub
  experiment keys, 24 per-site light/dark theme keys. On a mismatch, DO NOT stop and DO
  NOT guess: sweep the entire repo, gather all necessary context, resolve from source
  (the repo is truth; the manifest is the index), log the discrepancy in
  PARITY-REPORT.md, and proceed from the most complete, fully-realized design + backend
  spec found — never a reduced subset. Never build a component/page/hook/util without
  first checking the inventory — if it exists, port it; parallel implementations are
  violations.

Non-negotiables (full list + audit commands in DESIGN-CONTRACT.md):
  - PORT, DON'T RE-CREATE: all kit + per-site CSS files are copied VERBATIM
    (oh-tokens.css, oh-components.css, oh-site.css, oh-hub.css, cie.css, ce-*.css,
    os2t.css, orh.css, …). Never re-author them in Tailwind/CSS-in-JS/a UI kit.
  - JSX is transplanted: same element tree, same class names, same conditional logic.
    Converting window-globals to imports + adding types is expected; changing markup,
    classNames, styles, or copy is a violation.
  - ALL COPY IS VERBATIM — headlines, ledes, labels, empty states, banner text.
  - NO substitutions: no icon libraries (glyphs are unicode), no component libraries
    (shadcn/MUI/Chakra/Ant), no font swaps (Hanken Grotesk + IBM Plex Mono only),
    no new colors beyond each brand's one --accent from shared/products.js.
  - ONE ENGINE: all 21 OpenHubForAI registries render from a single makeHub port + config objects.
    Bespoke hub depth attaches only via entryExtra / extraRoutes / convert.render.
  - The A/B experiment engine (oh-experiments.js) ships with identical semantics and
    ALL declared variants (per-hub ledeVariants A/B/C, hero tests, ?exp= forcing,
    dataLayer events). Dropping variants is a violation.
  - PARITY GATE: a surface is done only after a 1280px screenshot is compared against
    openharness/screens/ and the live prototype — fonts, accent, layout, copy, glyphs,
    private-preview banner, dark mode, all routes. Fix mismatches; never declare them
    acceptable. Log every surface in PARITY-REPORT.md.
  - WHEN IN DOUBT, THE PROTOTYPE WINS. If a doc and the prototype disagree, match the
    prototype. If the stack truly can't match something, STOP and ask me — don't
    substitute.

Read in this order before writing code:
  1. openharness/DESIGN-CONTRACT.md  — enforcement rules + machine-checkable audits
  2. openharness/SYSTEM-INVENTORY.md — everything that already exists (DO NOT REBUILD)
  3. openharness/README.md           — family overview + the makeHub engine + flip-to-public
  4. openharness/CLAUDE-CODE.md      — orientation, what to port first, the prod gap
  5. openharness/IMPLEMENTATION-GUIDANCE.md — HARD vs FLEXIBLE + port order + DoD
  6. openharness/HANDOFF.md          — the implementation contract (§3.5 = makeHub)
  7. openharness/BACKEND-STACK.md    — per-registry backend each site needs
  8. openharness/screens/INDEX.md    — the reference image per surface
  9. the per-folder README.md for the surface you're building

Build order:
  1. Copy the kit CSS verbatim; transplant oh-site.jsx (chrome + primitive pages),
     then makeHub (oh-hub.jsx), then oh-experiments.js.
  2. Teleon (reference kit site) → run the parity gate on it before continuing.
  3. The 9 live hubs (config-only) + bespoke os2t/orh pages → parity gate each.
  4. Parent + Demo Control Tower → Baltor → the 12 private-bench hubs → parity gates.
  5. Only then: backend per BACKEND-STACK.md; precompiled JSX; real auth/persistence/
     billing; replace fixtures. Enforce status:'private' server-side.

All registry entries, corpora, runs, usage and receipts are illustrative fixtures.
Ask me before adding scope or content not in the prototypes.
```

---

## 2. Fidelity: **exact**
Final colors, type, spacing, dark mode, copy and interactions ship **as-is**. The CSS files
are production artifacts — copy them verbatim and transplant the JSX onto them (see
`DESIGN-CONTRACT.md` Rule 0). "Recreate in your own libraries" is exactly what caused the
last implementation to drift; it is now forbidden.

## 3. How to view the prototypes
Open any `*.html` in a browser — **no build step**. Entry files are listed in
`README.md` (the *Open each site* table). Start with
`context-is-everything/Context is Everything.html` (the parent) and
`context-is-everything/Demo Control Tower.html` (the operator index to every surface).

## 4. Architecture in one screen
- **`shared/`** is the whole design system + site kit. **Port it first** — every site renders
  from it. `oh-tokens.css` (only source of color) → `oh-components.css` (primitives + scale)
  → `oh-site.jsx` (chrome + primitive pages: auth, billing, settings, docs, …) →
  `oh-hub.jsx` `makeHub(cfg)` (a whole registry site from one config object).
- **21 OpenHubForAI registries are config-only** — each `<hub>/<hub>-main.jsx` is a `makeHub({…})` object +
  a `products.js` entry. 9 are live; **12 are a "private bench"** (`status:'private'`, muted
  accent + "Private preview" banner). Opening one = a one-line `status:'private' → 'live'` flip.
- **Bespoke per-hub depth** (OpenSkillToTool's `os2t-pages.jsx`, OpenReviewHub's `orh-pages.jsx`)
  attaches via gated hooks (`entryExtra` / `extraRoutes` / `convert.render`) — see `HANDOFF.md §3.5`.
- **Baltor** has its own `ce-*` chrome; **OpenHubForAI** has bespoke `pt-*` product pages — both reuse the
  shared primitives. **Teleon** is the cleanest reference (built entirely on the kit).

## 5. Prototype → production gap (must build)
1. Real toolchain — Vite/Next with **precompiled JSX** (in-browser Babel is prototype-only).
2. Backend + API + datastore per `BACKEND-STACK.md` (registry CRUD, signing/Rekor, eval/convert/
   review pipelines, durable state). Enforce `status:'private'` **server-side**.
3. Real auth, persistence, billing (all simulated now).
4. Replace every fixture with real data.

## 6. Legacy paths (intentional — don't "fix")
Folder/file names keep their original form (`context-is-everything/`, repo root `openharness/`,
`context-enrichment/` = Baltor) so ~20 cross-links don't break. The **displayed brand is "AI
Done Right" everywhere** (driven by `products.js`). Renaming paths requires a full reference sweep.

## 7. Verification status
All 24 surfaces render with zero horizontal overflow, light+dark clean, console clean (only the
expected in-browser Babel dev warning). Cross-link integrity checked (0 broken). The
**`Design Acceptance Scorecard.html`** is the branded-house consistency gate (family 94%).

## 8. Doc map
**`DESIGN-CONTRACT.md`** (enforcement rules — overrides everything) ·
**`SYSTEM-INVENTORY.md`** (manifest of everything that exists — reuse-first gate) ·
`README.md` (overview) ·
`CLAUDE-CODE.md` (orientation) · **`IMPLEMENTATION-GUIDANCE.md`**
(hard vs flexible constraints, port order, definition of done) · `HANDOFF.md` (contract) ·
`BACKEND-STACK.md` (backends) · `MARKETING.md` (copy) · `EXPERIMENTS.md` (A/B engine) ·
**`screens/INDEX.md`** (a reference image per surface) · `Design Acceptance Scorecard.html`
(gate) · `Demo Control Tower.html` (surface index) · per-folder `README.md` (file map per
site) · `openharnesshub/PAGES.md` (OpenHubForAI routes).
