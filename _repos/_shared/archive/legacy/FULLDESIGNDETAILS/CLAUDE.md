# Project memory — AI Done Right

Persistent context for anyone (human or agent) working in this project.

## What this is
**AI Done Right** (`aidoneright.dev`, tagline *"AI, done right."*) — a platform company
with two governed products and a family of open registries, all on one shared design system.
Everything lives under `openharness/` (the repo folder keeps its legacy name; see Rules).

- `context-is-everything/` — **AI Done Right**, the parent/portfolio site + **Demo Control
  Tower** (legacy folder/file names; displayed brand is "AI Done Right").
- `context-enrichment/` — **Baltor.ai**, paid SaaS · context assurance (folder/key is
  historically `context-enrichment`; the brand is **Baltor**).
- `teleon/` — **Teleon.dev**, purpose-driven runtime.
- **Live open hubs (.io):** `opencontexthub/` · `openskillshub/` · `opentoolshub/` ·
  `openskilltotool/` · `openmcphub/` · `opencompressionhub/` · `openbenchmarkhub/` ·
  `openreviewhub/` · `openharnesshub/`.
- **Private bench (built, `status:'private'`):** `opentemplateshub/` · `openendpointhub/` ·
  `openenvhub/` · `opensandboxhub/` · `openagenthub/` · `openreceipthub/` · `openstatehub/` ·
  plus 4 context-governance method hubs (Baltor engine stages): `openreconciliationhub/` ·
  `openhardeninghub/` · `openenrichmenthub/` · `openoptimizationhub/` · `openverificationhub/` —
  the 5 Baltor engine-stage method hubs (Reconcile · Harden · Enhance · Optimize · Verify).
- `shared/` — design tokens, canonical primitives, the **site kit** (`oh-site.*`,
  `oh-hub.*`), `cases.js`, `oh-experiments.js`, and `products.js` (brand + `PORTFOLIO`).

These are **prototypes** (HTML + React-via-Babel, mock data, no backend), used as the
implementation spec. Start at `openharness/README.md`, then `HANDOFF.md` / `CLAUDE-CODE.md`.
**`openharness/DESIGN-CONTRACT.md` governs any implementation handoff** — CSS/config ship
verbatim, JSX transplants with identical markup + class names, copy is verbatim, no
icon/component/font library substitutions, A/B engine + all variants ship, and every surface
passes the screenshot parity gate against `screens/` (logged in `PARITY-REPORT.md`).
**`openharness/SYSTEM-INVENTORY.md` is the reuse-first manifest** — implementers must print
its recognition table (24 surfaces · 21 hubs from one makeHub · 39 kit exports · 50 experiment
keys · 24 theme keys) and reconcile before coding; rebuilding anything on it is a violation.

Thesis across every property: **discovery is not trust** — turn open, discoverable AI
building blocks into governed, evidence-backed capability. The platform (Baltor/Teleon) is
the company; the `Open*Hub` sites are the open, top-of-funnel lead-gen.

## Rules to keep
- **Branded house**: identical scale/spacing/primitives/fonts/chrome across all sites;
  only the accent color differs. Live hubs use saturated accents; **private-bench hubs use a
  muted `accent` + a "Private preview" banner**, and store a saturated `futureAccent`.
- **Never hardcode colors/sizes** in a site stylesheet — use `shared/` tokens (`--accent`,
  `--fg`, `--line`, `--fs-*`, `--pad-*`, …).
- Every card surface = shared `.oh-card` (Baltor `.ce-*` + OHH `.pt-panel` compose it).
- **Build new kit sites on `shared/oh-site.jsx`**; registries on `makeHub()` in
  `shared/oh-hub.jsx`. A new brand = config + one inline `--accent`.
- **makeHub extension hooks** (opt-in, gated): `entryExtra(e)`, `extraRoutes[]`,
  `convert.render`, `access:'private'`. Bespoke hub code lives in the **site folder**
  (e.g. `openskilltotool/os2t-pages.jsx`, `openreviewhub/orh-pages.jsx`), not in the kit.
- **Flip-to-public:** opening a private hub = one line in `products.js`
  (`status:'private' → 'live'`). The accent resolver swaps muted→`futureAccent` and the
  banner clears automatically (parent, hub, Control Tower).
- Brand names/taglines + the portfolio live only in `shared/products.js` (`BRAND`/`GROUP`/
  `ENTITIES`/`LAYERS`) — one-line renames. The parent + Control Tower render from it.
- **Legacy paths, current brand:** keep folder/file names (`context-is-everything/Context is
  Everything.html`, repo root `openharness/`) — ~20 cross-links depend on them. Only the
  *displayed* brand changed to "AI Done Right". Don't rename paths without sweeping refs.
- Each folder has a `README.md`; keep them current when structure changes.
- Don't reintroduce the retired `.oh.brand-ce` scope — Baltor uses `dir-d`.
- Baltor predates the kit (own `ce-*` router/chrome) but reuses shared `.oh-*` primitives —
  keep it visually in-house; don't fork the card/scale.
