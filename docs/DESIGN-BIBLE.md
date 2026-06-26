# THE DESIGN BIBLE: AI Done Right, the single designer-ready product-design reference

> The visual and UX counterpart to `docs/BIBLE.md` (the what, why, and laws). This is the "how it looks and how it is
> built", detailed enough to hand to a designer (a human or Claude acting as designer) so they can understand,
> reproduce, and extend the product, especially the logged-in AIDevObserver app. Every value here is quoted from the
> source code (No Magic Values applies to design too): never re-hardcode a token, and the file the value lives in is
> named in line. This doc is one of the five CANONICAL docs tracked by `scripts/check_context_freshness.py`
> (`CLAUDE.md`, `AGENTS.md`, `docs/NORTHSTAR.md`, `docs/BIBLE.md`, `docs/DESIGN-BIBLE.md`), so keep its file references
> real. Last reconciled 2026-06-26. `serves_truth = false` (the surfaces render candidate output; only Baltor's
> governed source answers serve truth).

**This is a near-rewrite. The prior version named `scripts/surface_server.py` as THE canonical renderer. That is
SUPERSEDED.** The canonical product is the set of full apps under `web/<app>/`, served by the showcase server over the
shared kit, with the service-plane backends behind same-origin seams. `scripts/surface_server.py` is now a lightweight
fallback only (see the one-line note in section 1). The reconciliation is recorded inside this section so the
contradiction is closed, not orphaned.

**Single sources this doc is generated from (read these; do not trust the prose over the code):**

| Source file | What it is |
|---|---|
| `scripts/showcase/server.py` | THE canonical renderer. `python3 -m scripts.showcase` serves `web/<OH_PRODUCT>/` (the full app) and proxies the service plane behind same-origin seams. `WEB_DIR = web/<OH_PRODUCT>`. |
| `web/teleon/kit/oh-tokens.css` | The token palette (radii, fonts, neutrals, accent, semantic colors, primitive hues) for every scope. The shipped family scope is `.oh.dir-s.theme-light`. |
| `web/teleon/kit/oh-components.css` | The component layer and the canonical type, spacing, and chrome scale (`--fs-*`, `--pad-*`, `--maxw-site`). Atoms: `.oh-btn`, `.oh-card`, `.oh-badge`, `.oh-table`, `.oh-field`, `.oh-input`. |
| `web/teleon/kit/oh-site.css` | The site and app layout CSS: top bar, hero, sections, footer, and the logged-in app shell (`.ohs-app`, `.ohs-side`, `.ohs-main`, `.ohs-topbar`). |
| `web/teleon/kit/oh-site.jsx` | The shared kit React components: `OhTopBar`, `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhFooter`, `OhAppShell`, `OhPageHead`, `OhRollup`, plus hooks (`useHashRoute`, `navigate`, `useSiteTheme`). |
| `web/teleon/kit/products.js` | The brand and product registry (single source). `PORTFOLIO.ENTITIES.<id>.accent` is the per-brand accent for Teleon, Baltor, and AIDevObserver. |
| `architecture/surface_capability_spec.json` | `pillars[]`: id, accent, brand, role, and `canonical_surface` per surface; the `serving_rule`. Source of the AI Done Right (`#5a6b87`) and OpenHubForAI (`#3b6fd4`) accents. |
| `architecture/local_service_registry.json` + `architecture/identity_realm_registry.json` | The single source of local service ports the showcase reads to build the `/api/*` and `/registry/` seams. |
| `docs/concepts/component-taxonomy-and-stages.md` | The seven primitives (Input, Knowledge Corpus, If Statement, Action, Loop, Stop/End, Output). |
| `docs/standards/DESIGN.md` + `docs/standards/design-principles.md` | The existing design standards this bible extends. |

---

## 1. The one design law and the canonical stack

**ONE design system. Every surface composes the SAME shared kit. The accent color and the copy are the only
per-surface variables.**

The standardization point is stated in the code itself. `web/teleon/kit/oh-components.css` declares the scale as
"ONE type/space/chrome scale shared by every site. Sites differ ONLY by accent color (token scope). Padding, font
sizes, chrome dimensions and the display face are identical everywhere." A surface is therefore never styled from
scratch. It sets a root scope class and overrides one value:

```jsx
<div className={'oh dir-s theme-' + theme + ' oh-site tln'} style={{ '--accent': ACCENT }}>
```

That single line (from `web/teleon/teleon-main.jsx`, mirrored in `web/aidevobserver/aidevobserver-main.jsx`) is the
whole per-surface contract: the `oh dir-s theme-light oh-site` scope pulls in the shared tokens and components, and
`--accent` is the one brand variable.

### The canonical stack (four layers)

1. **The apps.** Five full front-end apps live under `web/<app>/`: `context-is-everything` (AI Done Right),
   `teleon`, `baltor`, `harness-hub` (OpenHubForAI), and `aidevobserver`. Each app is its own entry HTML plus a small
   brand main file (for example `web/teleon/index.html` + `web/teleon/teleon-main.jsx` + `web/teleon/teleon.css`).
2. **The showcase server.** `scripts/showcase/server.py` is the renderer. `OH_PRODUCT` picks the folder and
   `WEB_DIR = web/<OH_PRODUCT>` is served at the origin root. Run it with `python3 -m scripts.showcase --port <N>`.
3. **The shared kit.** Every app loads the same files from its `kit/` folder: `oh-tokens.css`, `oh-components.css`,
   `oh-site.css`, `oh-site.jsx`, and `products.js` (plus `oh-identity.js`, `oh-registry.js`, `cases.js`,
   `oh-experiments.js`). Chrome and primitive pages come from the kit; only brand config and a few bespoke pieces are
   local to the app.
4. **The service plane.** The showcase proxies same-origin seams (`/api/*`, `/registry/`, `/analytics/`) to the local
   service backends, with ports read from `architecture/local_service_registry.json` and
   `architecture/identity_realm_registry.json`. The front-end declares the bases it expects:
   `window.OHH_IDENTITY_BASE = ''`, `window.OHH_REGISTRY_BASE = '/registry'`, `window.OHH_EVENTS_BASE = '/analytics'`.

### Reconciliation (the contradiction, closed)

- **Superseded:** the prior bible documented `scripts/surface_server.py` as THE canonical renderer, with a
  byte-identical `_CSS_TEMPLATE` and a fixed `dir-a.theme-light` palette (`--bg #faf7f0`). That described a thin
  standalone renderer, not the shipped product.
- **Canonical now:** the shipped product is the full app in `web/<app>/`, served by `python3 -m scripts.showcase`
  over the shared kit, with the service plane behind seams. The real palette is `web/<app>/kit/oh-tokens.css`,
  `.oh.dir-s.theme-light` (`--bg #fafaf8`), with the accent overridden per brand. The same conclusion is encoded in
  `architecture/surface_capability_spec.json`, whose `serving_rule` reads: "Launchers MUST serve each pillar's
  `canonical_surface` (the built-out `web/*` app)", and whose `canonical_surface` fields point at `web/context-is-everything`,
  `web/teleon`, `web/baltor`, and `web/harness-hub`.
- **`scripts/surface_server.py` is a lightweight FALLBACK only.** It can render a minimal standalone surface when the
  full app or the service plane is not available. It is not canonical and a designer never edits it to change the look.

---

## 2. The five surfaces

The family is one holding brand (AI Done Right) over four products. Each surface is a full app served by the showcase
with its own `OH_PRODUCT`. Accents come from `web/<app>/kit/products.js` (Teleon, Baltor, AIDevObserver) and from
`architecture/surface_capability_spec.json` (AI Done Right, OpenHubForAI). Roles below are written in clean product
copy (the raw spec strings are paraphrased per the copy rules in section 8).

| Brand | `OH_PRODUCT` / web dir | Accent | Role | Primary backend seam |
|---|---|---|---|---|
| AI Done Right | `context-is-everything` | `#5a6b87` (slate blue) | Parent holding brand. The portfolio home that introduces the family. | identity, registry, analytics (marketing and portfolio) |
| Teleon | `teleon` | `#6d5ef0` (indigo) | The purpose-driven, eval-gated, self-adaptive compute runtime. | `/api/teleon/` (`teleon_local_runtime`) |
| Baltor | `baltor` | `#0e7c86` (teal) | Managed, verified, provable context, powered by Teleon (governs truth). | the live-ops family (`/api/demo/`, `/api/context/`, `/api/pipeline/`, `/api/runtime/`) via `baltor_admin_demo_server` |
| AIDevObserver | `aidevobserver` | `#b25fd6` (orchid) | Reviews how a team uses AI coding agents and turns each session into a clear, ranked report. | identity, registry, analytics (review engine: `src/teleon/observer`) |
| OpenHubForAI | `harness-hub` | `#3b6fd4` (royal blue) | The open store of context, tools, skills, and harnesses that both products consume, plus the open CapabilityTask spec. | `/registry/` (`local_openhub_projection_api`) plus `/api/components` and `/api/primitives` |

Notes. The `aidevobserver` accent (`#b25fd6`) lives only in `web/aidevobserver/kit/products.js`, the build-out target.
The teal `#0e7c86` doubles as the family's `--verified` color (the "verified" read). Every surface shares the
identity, registry, and analytics seams; the table lists each surface's distinctive backend.

---

## 3. The seven primitives in the product UI

Everything a pipeline does reduces to seven primitives (single source: `docs/concepts/component-taxonomy-and-stages.md`,
backed by `scripts/primitives/base.py`). They are the product's core vocabulary, so the UI names and colors them
consistently. Use the product label in user-facing copy, never the internal schema `type`.

| # | Primitive | What it is | Legend hue (token, `.oh.theme-light`) |
|---|---|---|---|
| 1 | **Input** | The payload to work on. | `--p-input` `#5b6470` |
| 2 | **Knowledge Corpus** | A store of facts, queried by a trigger. | `--p-knowledge` `#1a7f37` |
| 3 | **If Statement** | The condition (the IF), kept separate from the THEN. | `--p-conditional` `#9a6700` |
| 4 | **Action** | Anything that does something (the THEN): a persona, tool, processor, harness, or rubric. | `--p-action` `#c2410c` |
| 5 | **Loop** | Control flow and iteration over sub-steps. | `--p-loop` `#6e40c9` |
| 6 | **Stop / End** | Halt early on a guard or terminal condition. | `--p-stop` `#cf222e` |
| 7 | **Output** | Finalize the result and the trace. | `--p-output` `#0969da` |

Where they show up:

- **The legend and pipeline nodes.** The seven hues (`--p-*` in `web/teleon/kit/oh-tokens.css`) color the node chips
  and the legend in any pipeline or flow view. The light-theme set is darkened for AA contrast on paper.
- **The OpenHubForAI store.** The showcase serves `/api/primitives` (from `scripts/primitives`) and `/api/components`,
  so the browse and store views group catalog components under their primitive.
- **Product copy.** Say "Knowledge Corpus" (not "knowledge pack"), "If Statement" (not "rule pack"), and "Action"
  (a persona, tool, processor, harness, or rubric is an Action). Version lives in metadata, never in a name or ID.

---

## 4. Tokens

The real token palette is `web/<app>/kit/oh-tokens.css`. The file defines six-plus scopes (`dir-a` through `dir-s`,
each with `theme-light` and `theme-dark`). The family ships the synthesis scope `.oh.dir-s.theme-light` (the "Harness
House Style", light theme): it is the scope the live new apps render (`oh dir-s theme-light` in
`web/teleon/teleon-main.jsx` and `web/aidevobserver/aidevobserver-main.jsx`). The accent is then overridden per brand
inline. All values below are quoted from `.oh.dir-s.theme-light` (and the shared `.oh` block).

### Neutrals, accent, and semantic colors (`.oh.dir-s.theme-light`)

| Token | Value | Meaning |
|---|---|---|
| `--bg` | `#fafaf8` | page background (warm near-white) |
| `--bg-subtle` | `#f1f0ec` | one step down: hovers, code wells, inset fields |
| `--panel` | `#ffffff` | raised card and panel surface |
| `--panel-2` | `#f8f7f3` | secondary panel fill |
| `--line` | `#e7e5dd` | hairline border and divider |
| `--line-strong` | `#d5d2c7` | stronger border (inputs, emphasis) |
| `--fg` | `#161513` | primary ink |
| `--fg-muted` | `#66635b` | secondary text (ledes, body, labels) |
| `--fg-faint` | `#868277` | tertiary and metadata text |
| `--accent` | per brand (overridden inline) | the one brand variable; default in scope is `#d6553a` |
| `--accent-ink` | `#ffffff` | text and ink on an accent fill |
| `--accent-weak` | `#fbede7` | accent tint for the active sidebar item and soft fills |
| `--success` | `#1a7f37` | success |
| `--warning` | `#9a6700` | warning |
| `--danger` | `#c0392b` | danger |
| `--info` | `#1f6fb2` | info |
| `--verified` | `#0e7c86` | the verified read (also Baltor's brand teal) |

Tinted derivations track the accent with `color-mix`, not parallel literals, for example
`color-mix(in srgb, var(--accent) 35%, var(--line))` for an accent-tinted border. Spend the accent on intent (the
primary action, the active item, the brand mark, a focused field); everything structural is a neutral token.

### Type scale (shared `.oh`, in `web/teleon/kit/oh-components.css`)

The UI font is **Inter** (`--font-sans: "Inter", -apple-system, "Segoe UI", system-ui, sans-serif`). The display face
in `dir-s` is **Hanken Grotesk** (`--font-display: "Hanken Grotesk", "Inter", sans-serif`). Mono is
`--font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace`. Light theme. The reference entry HTML
`web/aidevobserver/index.html` loads all three from Google Fonts (`Inter`, `Hanken Grotesk`, `JetBrains Mono`,
weights 400 to 800).

| Token | Value | Role |
|---|---|---|
| `--fs-h1` | `clamp(34px, 4.6vw, 52px)` | hero H1 (line-height 1.05, letter-spacing -.03em, display face) |
| `--fs-h2` | `clamp(26px, 3.2vw, 34px)` | section H2 and band H2 |
| `--fs-h3` | `19px` | feature and card H3 / H4 |
| `--fs-page-title` | `30px` | logged-in page title (`.ohs-pagehead h1`) |
| `--fs-lead` | `18px` (`--lh-lead 1.58`) | hero lede |
| `--fs-body` | `15px` (`--lh-body 1.6`) | body and section copy |
| `--fs-eyebrow` | `11px` (`--ls-eyebrow .14em`) | uppercase kicker above a title |
| `--fs-small` | `13px` | small print |

### Radii, spacing, shadows, chrome (shared `.oh` and `dir-s`)

| Token | Value | Use |
|---|---|---|
| `--r-sm` | `6px` | inputs, small chips |
| `--r-md` | `9px` | buttons, sidebar links, most cards |
| `--r-lg` | `12px` | the `.oh-card` surface |
| `--r-pill` | `999px` | pills, segmented controls, switches |
| `--pad-card` | `22px` | `.oh-card--pad` padding |
| `--pad-panel` | `28px` | panel padding |
| `--maxw-site` | `1120px` | marketing content width |
| `--w-sidebar` | `240px` | sidebar scaffold width (the app shell grid uses `248px`) |
| `--h-topbar` | `64px` | marketing top bar height |
| `--e1` | `0 1px 2px rgba(40,30,20,.05)` | resting card shadow (warm-brown, not gray) |
| `--e2` | `0 12px 34px rgba(40,30,20,.11)` | hover lift and raised aside cards |
| `--ease` | `cubic-bezier(.2,.8,.2,1)` | the shared transition curve |

### The five accents (single source per surface)

| Surface | `--accent` | Source |
|---|---|---|
| AI Done Right | `#5a6b87` | `architecture/surface_capability_spec.json` |
| Teleon | `#6d5ef0` | `web/teleon/kit/products.js` (`PORTFOLIO.ENTITIES.teleon.accent`) |
| Baltor | `#0e7c86` | `web/baltor/kit/products.js` (`PORTFOLIO.ENTITIES.baltor.accent`) |
| AIDevObserver | `#b25fd6` | `web/aidevobserver/kit/products.js` (`PORTFOLIO.ENTITIES.aidevobserver.accent`) |
| OpenHubForAI | `#3b6fd4` | `architecture/surface_capability_spec.json` |

Contrast: every accent is AA on `--panel` and `--bg`; `--accent-ink` (white) is the only thing placed on an accent
fill.

---

## 5. The shared kit components

Documented from the real components in `web/teleon/kit/oh-site.jsx` and the classes in `oh-site.css` and
`oh-components.css`. Two atoms underpin everything: the button and the card.

### Atoms: button and card (`oh-components.css`)

```jsx
<button className="oh-btn oh-btn--primary">Start free</button>   {/* accent fill, --accent-ink text */}
<button className="oh-btn oh-btn--ghost">See how it works</button> {/* transparent, --line border */}
<button className="oh-btn oh-btn--primary oh-btn--sm">Install</button> {/* compact: 7px 12px, 13px */}

<div className="oh-card oh-card--pad">…</div>            {/* --panel surface, --line border, --r-lg, 22px pad */}
<div className="oh-card oh-card--pad oh-card--interactive">…</div> {/* adds hover lift to --e2 + accent border */}
```

`.oh-btn` is `font-size 14px / weight 650`, `border-radius var(--r-md)`, `padding 10px 18px`, `inline-flex` with
`gap 8px`. `.oh-card` is `1px solid var(--line)`, `background var(--panel)`, `border-radius var(--r-lg)`. Use one
primary button per view. Status reads use `.oh-badge` with a variant: `--verified` (teal), `--warn` (amber),
`--danger` (red), `--muted` / `--stable` (gray), `--sm` for the compact size.

### 5.1 `OhTopBar` (marketing chrome)

`<header className="ohs-top">`: the brand logo (`OhLogo`, an accent mark plus the name), the portfolio switcher
(`OhPortfolioMenu`), a spacer, the nav links, then the right cluster (theme toggle, optional Sign in, a primary CTA).
Props: `brand, nav, cta, signInHref, theme, onToggle`.

```jsx
<OhTopBar brand={BRAND} nav={MKT_NAV} cta={{ label: 'Install', href: '/runs' }}
  theme={theme} onToggle={onToggle} />
```

### 5.2 `OhHero`

`<section className="ohs-hero">` with `.ohs-wrap` (adds `.ohs-hero-grid`, a `1.08fr .92fr` two-column grid, when an
`aside` is given): an eyebrow, an `<h1>` (a `.tint` span inside the title is colored with the accent), a `.lede`, a
`.ohs-cta` button row, and the optional aside card. Props: `eyebrow, title, lede, ctas, aside`.

```jsx
<OhHero eyebrow="AI coding session review"
  title={<>See how your team really uses <span className="tint">AI coding agents</span>.</>}
  lede="AIDevObserver turns each session into a clear, ranked report."
  ctas={[{ label: 'See a review', onClick: () => scrollToId('demo'), primary: true },
         { label: 'Install the extension', onClick: () => scrollToId('runs') }]}
  aside={<HeroReviewCard />} />
```

### 5.3 `OhSection`

`<section className="ohs-section" id={id}>` with `.ohs-wrap`: an `.ohs-section-label` kicker, an `<h2>`, an
`.ohs-body` lede, and `children`. The `id` lets in-page nav scroll to it. Props: `label, title, body, children, id`.

```jsx
<OhSection id="how" label="How it works" title="A session goes in. A clear, ranked report comes out."
  body={<>It flags reinvention, wasted context, risky commands, and missed cheaper paths.</>}>
  <OhFeatures items={HOW} />
</OhSection>
```

### 5.4 `OhFeatures`

A `.ohs-grid-3` of `.oh-card.ohs-feature` cards, each a `.fi` glyph, an `<h4>`, and a `<p>`. Props: `items` as
`[[glyph, title, desc], ...]`.

```jsx
<OhFeatures items={[
  ['◉', 'Every session becomes a report', 'A short, ranked report you can read in under a minute.'],
  ['⚑', 'It flags what actually costs you', 'Reinvention, wasted context, risky commands, missed cheaper paths.'],
  ['↑', 'Ranked by confidence', 'High-confidence findings rise; low-signal noise drops away.'],
]} />
```

### 5.5 `OhBand`

A full-width call-to-action band: `<section className="ohs-band">` with an `<h2>`, an optional `<p>`, and a
`.ohs-cta` button row. Props: `title, sub, ctas`.

```jsx
<OhBand title="Make every AI coding session count."
  sub="Turn raw agent sessions into reports your team actually learns from."
  ctas={[{ label: 'Install the extension', href: '/runs', primary: true },
         { label: 'See a review', href: '/demo' }]} />
```

### 5.6 `OhFooter`

`<footer className="ohs-foot">` with `.ohs-foot-grid`: the brand mark and an `.ohs-foot-tag` tagline on the left, then
`.ohs-foot-cols` of `.ohs-foot-col` link columns. Props: `brand, tagline, cols` as `[[heading, [[label, href], ...]], ...]`.

```jsx
<OhFooter brand={BRAND} tagline="AI coding session review, part of AI Done Right" cols={[
  ['Product', [['How it works', '/how'], ['Where it runs', '/runs'], ['Trust', '/trust']]],
  ['Family', [['AI Done Right', '../context-is-everything/index.html'], ['Teleon', '../teleon/index.html']]],
]} />
```

### 5.7 `OhAppShell` (logged-in chrome): see section 6b

### 5.8 `OhPageHead` and `OhRollup` (logged-in page atoms)

`OhPageHead` is the in-app page header: `.ohs-pagehead` with an eyebrow, an `<h1>` (`--fs-page-title`), a `<p>` sub,
and an `.ohs-pagehead-actions` slot. `OhRollup` is a row of stat cards: `.ohs-rollup` of `.oh-card.ohs-roll`, each a
`.v` value over a `.k` label. Props: `OhPageHead({ eyebrow, title, sub, actions })`, `OhRollup({ items })` where
items are `[[label, value], ...]`.

```jsx
<OhPageHead eyebrow="Workspace" title="Sessions"
  sub="Each AI coding session, reviewed and ranked." actions={<button className="oh-btn oh-btn--primary">Review latest</button>} />
<OhRollup items={[['Sessions, 30d', 128], ['High findings', 14], ['Avg confidence', '0.91']]} />
```

### Cards, pills, table, fields

`.oh-card` is the one surface for every card and panel. `.oh-table` is the data table (uppercase 11px headers,
12px cell padding, `--line` row borders). `.oh-field` wraps a labeled input; `.oh-input` is a standalone input; both
focus to an accent border. `.oh-segment` is a pill-shaped segmented control. `.oh-kbd` renders a keyboard hint
(for example the `Command K` palette). Build new pieces from these tokens, never raw hexes.

---

## 6. Layout: two layouts, one family

Both layouts use the same kit, the same tokens, and the same accent. They differ only in chrome: marketing pages have
a top nav; logged-in pages have a left sidebar.

### 6a. Marketing and home pages (the public pattern)

Top nav, hero, sections, cards, band, footer. This is `web/teleon/index.html` plus `web/teleon/teleon-main.jsx`
(`Landing`), and `web/aidevobserver/aidevobserver-main.jsx` (`Landing`). The structure:

```jsx
<div className={'oh dir-s theme-' + theme + ' oh-site tln'} style={{ '--accent': ACCENT }}>
  <OhTopBar brand={BRAND} nav={MKT_NAV} cta={{ label: 'Start free', href: '/signup' }} theme={theme} onToggle={onToggle} />
  <OhHero eyebrow={…} title={…} lede={…} ctas={[…]} aside={<HeroCard />} />
  <OhSection id="how" label="How it works" title={…} body={…}><OhFeatures items={…} /></OhSection>
  {/* more sections */}
  <OhBand title={…} sub={…} ctas={[…]} />
  <OhFooter brand={BRAND} tagline={…} cols={[…]} />
</div>
```

`.ohs-hero` is `padding 76px 0 60px` with a bottom `--line`. The hero H1 is `--fs-h1` in the display face; the lede is
`--fs-lead`, `--fg-muted`, capped at `60ch`. Content centers in `--maxw-site` (1120px). On narrow screens the hero
grid collapses to one column and the H1 drops to `40px`.

### 6b. Logged-in and app pages (the left-sidebar pattern)

A left sidebar plus a content area, the Control Tower and dashboard pattern. The canonical implementation is the kit's
`OhAppShell` (`web/teleon/kit/oh-site.jsx`), which `web/teleon/teleon-main.jsx` uses for its logged-in routes
(`APP_NAV`). Existing logged-in surfaces in the same family: the Teleon Control Tower
(`web/teleon/Teleon PurposeTask Control Tower.html`), the Baltor dashboards (`web/baltor/dashboard.html` and the
guided demos), and the OpenHubForAI admin demo (`web/harness-hub/admin-demo.html`).

```jsx
<OhAppShell brand={BRAND} nav={APP_NAV} route={route} cta={{ label: '+ New run', href: '/runs' }}
  theme={theme} onToggle={onToggle}
  header={<button className="ohs-side-search">Search… <span className="oh-kbd">⌘K</span></button>}>
  {page}
</OhAppShell>
```

The shell renders as a CSS grid:

```css
.ohs-app  { display: grid; grid-template-columns: 248px 1fr; min-height: 100vh; }
.ohs-side { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; padding: 22px 16px; }
.ohs-main { /* the content area */ }
```

- **The left sidebar (`.ohs-side`).** Top to bottom: `.ohs-side-top` (the brand logo), an optional `header` slot (the
  search and Command K trigger), `.ohs-side-nav` (the nav links), and `.ohs-side-foot` (a primary CTA, a Settings
  link, and the theme toggle). The sidebar is `position: sticky; height: 100vh`, so it stays put while the content
  scrolls.
- **The nav links (`.ohs-side-link`).** Each is `[href, glyph, label]`. A `.g` glyph sits left of the label. The
  active link gets `.on`, which fills it with `--accent-weak` and colors it `--accent`. Pass `nav` as a flat
  `[[href, glyph, label], ...]` list, or `groups` (collapsible `OhNavGroup` sections) for a longer app.
- **The content area (`.ohs-main`).** Holds an optional sticky `.ohs-topbar` (height 54px, for an account or context
  bar), an honest preview banner, then the page. Pages open with `OhPageHead`, often an `OhRollup`, then `.oh-card`
  content.
- **The top bar with account.** The in-app `.ohs-topbar` is the place for account context (workspace name, the
  signed-in user, environment). The marketing top bar carries Sign in and the CTA instead.
- **Consistency with marketing.** Same scope (`oh dir-s theme-light`), same tokens, same accent, same type scale,
  same `.oh-card` and `.oh-btn` atoms. A logged-in page is the marketing design with the chrome swapped from a top
  nav to a left sidebar, nothing more.
- **Responsive.** Below the kit breakpoint the grid becomes one column and the sidebar un-sticks to a horizontal row
  (`.ohs-side { position: static; flex-direction: row; flex-wrap: wrap; }`).

---

## 7. Consistency rules

These are the family invariants. Hold them on every surface.

- **One shared kit, everywhere.** Every surface loads the same `kit/` files (`oh-tokens.css`, `oh-components.css`,
  `oh-site.css`, `oh-site.jsx`, `products.js`). Chrome and primitive pages come from the kit. Do not fork the kit per
  surface.
- **One marketing layout.** Every home page is top nav, hero, sections, cards, band, footer, built from `OhTopBar`,
  `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhFooter`.
- **One logged-in shell.** Every app page uses the `OhAppShell` left-sidebar shell with `OhPageHead`, `OhRollup`, and
  `.oh-card` content.
- **Differ only by accent and copy.** The per-surface variables are `--accent` (one inline override) and the brand
  copy (`products.js` plus the app's section text). Nothing else changes between surfaces.
- **Bespoke pieces compose tokens.** When a surface needs a piece the kit lacks (for example AIDevObserver's findings
  list), add a small scoped stylesheet (`web/<app>/<app>.css`) that builds only from `var(--token)` values and
  `color-mix` off `--accent`. Never introduce a raw hex or a parallel scale.

---

## 8. Copy rules (hard rules)

These are owner design rules. They are not suggestions. They extend `docs/standards/DESIGN.md` and
`docs/standards/design-principles.md`. Follow them in product copy and in this bible's own prose.

1. **No placeholders.** Write the real name and the real words. Write "OpenHubForAI", never "Open*Hubs". Write
   "AIDevObserver", "AI Done Right", "Teleon", "Baltor". No "Lorem ipsum", no "TODO", no "coming soon", no "[brand]".
   Every visible string ships as final copy.
   - Wrong: "Open*Hubs, coming soon." Right: "OpenHubForAI: the open store both products consume."
2. **No em dashes or en dashes, anywhere.** Do not use the long dash or the medium dash in any copy or in this doc.
   Use a comma, a period, parentheses, or a colon instead. (Regular hyphens inside words like "left-sidebar" and
   "logged-in" are fine; the middot separator is fine.)
   - Wrong: "One review, wherever your team works, post session." with a long dash between clauses. Right: "One review,
     wherever your team already works."
3. **No strategy leakage in public copy.** Public copy never says "moat", "wedge", "private bench", "win one
   vertical", or names a competitor as a target, and never states pricing or competitive strategy as positioning. Sell
   the product and its value, not the business plan.
   - Wrong: "Our wedge into the agent market." Right: "Reviews how your team uses AI coding agents and turns each
     session into a clear, ranked report."
4. **Real, confident sales and marketing copy.** Lead with the outcome for the customer. Be specific and plain.
   AIDevObserver's live copy is the reference: "See how your team really uses AI coding agents", "A session goes in. A
   clear, ranked report comes out.", "Findings are suggestions a person triages."

---

## 9. Claude Design handoff: build out the AIDevObserver product design

AIDevObserver (`web/aidevobserver/`, accent `#b25fd6`) currently ships the marketing app
(`aidevobserver-main.jsx` renders `Landing` only). The build-out is the **logged-in app**: the left-sidebar shell and
its views. The review engine backend is `src/teleon/observer`; this handoff is the front-end design.

### The logged-in app shell (left sidebar)

Use `OhAppShell` with the AIDevObserver accent. Sidebar nav (the `[href, glyph, label]` shape used by `APP_NAV` in
`web/teleon/teleon-main.jsx`):

| Route | Glyph idea | Label | View |
|---|---|---|---|
| `/sessions` | `▤` | Sessions | The list of reviewed AI coding sessions (an `OhRollup` plus an `.oh-table`: session, surface, duration, top finding, confidence). |
| `/review` | `◉` | Review report | The full ranked report for one session: a summary card, then the ranked findings. |
| `/findings` | `⚑` | Findings | Findings across sessions, filterable by type and severity, each with a confidence bar. |
| `/settings` | `⚙` | Settings | Surfaces (VS Code, Cursor, Claude Code MCP, CLI), what is reviewed, retention. |

### The review-report view (ranked findings plus confidence)

Reuse the bespoke pieces already in `web/aidevobserver/aidevobserver.css`: `.ado-finding` (a finding row with a
`sev-high` / `sev-medium` severity dot and accent border tint) and `.ado-conf` (the confidence bar plus percent).
The marketing demo (`ReviewDemo`, `FindingRow`, `ConfBar`) already renders exactly this; lift it into the logged-in
view inside `OhAppShell`:

```jsx
function ReviewReport({ session }) {
  const ranked = session.findings.slice().sort((a, b) => b.conf - a.conf);
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Session review" title={session.title}
        sub="Findings ranked by confidence. Suggestions a person triages, never gates." />
      <OhRollup items={[['Findings', ranked.length], ['High severity', ranked.filter(f => f.sev === 'high').length],
        ['Top confidence', Math.round(ranked[0].conf * 100) + '%']]} />
      <div className="oh-card oh-card--pad">
        <div className="ado-findings">{ranked.map(f => <FindingRow f={f} key={f.type} />)}</div>
      </div>
    </div>
  );
}
```

Findings rank by confidence (high first), so the most useful finding is the first one read. Keep the four finding
types from the live app: Risky command, Reinvention, Wasted context, Missed cheaper path. Hold the product promise in
the copy: read-only, suggestions not gates, nothing stored.

### Safe to change vs locked

| Safe to change | Locked (do not break) |
|---|---|
| The AIDevObserver accent (`#b25fd6` in `web/aidevobserver/kit/products.js`). | The shared kit: `oh-tokens.css`, `oh-components.css`, `oh-site.css`, `oh-site.jsx`, `products.js`. Edit per-app files, never the kit, to change one surface. |
| Brand copy and section text in `aidevobserver-main.jsx`. | The two-layout family: marketing is top nav plus hero; logged-in is the `OhAppShell` left sidebar. Do not invent a third chrome. |
| Add a bespoke, token-built piece in `web/aidevobserver/aidevobserver.css` (a new card, a chart). | The copy rules in section 8 (no placeholders, no em or en dashes, no strategy leakage). |
| New app pages and routes for the logged-in views above. | The accent-only per-surface rule: never add a per-surface fork of the kit or a parallel token scale. |

### Read order for the designer

1. This doc, sections 1, 2, 6, 7, 8 (the stack, the surfaces, the two layouts, consistency, copy rules).
2. `web/aidevobserver/aidevobserver-main.jsx` and `web/aidevobserver/aidevobserver.css` (the existing marketing app and
   its bespoke pieces).
3. `web/teleon/teleon-main.jsx` (the reference for the `OhAppShell` left-sidebar logged-in app: `App`, `APP_NAV`).
4. `web/teleon/kit/oh-site.jsx` (the kit components and `OhAppShell`) and `web/teleon/kit/oh-tokens.css` (the tokens).
5. `web/harness-hub/admin-demo.html` and `web/teleon/Teleon PurposeTask Control Tower.html` (existing logged-in
   dashboards in the family).

---

## Appendix: file map

| Concern | File |
|---|---|
| Canonical renderer (`OH_PRODUCT`, `WEB_DIR`, seams) | `scripts/showcase/server.py` (run `python3 -m scripts.showcase`) |
| Lightweight fallback renderer (not canonical) | `scripts/surface_server.py` |
| Tokens (palette, fonts, primitive hues) | `web/teleon/kit/oh-tokens.css` |
| Components and type scale | `web/teleon/kit/oh-components.css` |
| Site and app-shell layout CSS | `web/teleon/kit/oh-site.css` |
| Shared kit React components and hooks | `web/teleon/kit/oh-site.jsx` |
| Brand and product registry (accents) | `web/teleon/kit/products.js`, `web/aidevobserver/kit/products.js` |
| Surface spec (id, accent, brand, role, canonical_surface) | `architecture/surface_capability_spec.json` |
| Service-plane ports | `architecture/local_service_registry.json`, `architecture/identity_realm_registry.json` |
| The seven primitives | `docs/concepts/component-taxonomy-and-stages.md` |
| Existing design standards | `docs/standards/DESIGN.md`, `docs/standards/design-principles.md` |
| Teleon marketing app | `web/teleon/index.html`, `web/teleon/teleon-main.jsx`, `web/teleon/teleon.css` |
| AIDevObserver app (build-out target) | `web/aidevobserver/index.html`, `web/aidevobserver/aidevobserver-main.jsx`, `web/aidevobserver/aidevobserver.css` |
| Logged-in dashboard references | `web/harness-hub/admin-demo.html`, `web/baltor/dashboard.html` |
| Context-freshness guard (this is 1 of the 5 canonical docs) | `scripts/check_context_freshness.py` |
