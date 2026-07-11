# THE DESIGN BIBLE: AI Done Right, the single designer-ready product-design reference

> The visual and UX counterpart to `docs/BIBLE.md` (the what, why, and laws). This is the "how it looks and how it is
> built", detailed enough to hand to a designer (a human or Claude acting as designer) so they can understand,
> reproduce, and extend the product, especially the logged-in AIDevObserver app. Every value here is quoted from the
> source code (No Magic Values applies to design too): never re-hardcode a token, and the file the value lives in is
> named in line. This doc is one of the five CANONICAL docs tracked by `scripts/check_context_freshness.py`
> (`CLAUDE.md`, `AGENTS.md`, `docs/NORTHSTAR.md`, `docs/BIBLE.md`, `docs/DESIGN-BIBLE.md`), so keep its file references
> real. Last reconciled 2026-06-26. `serves_truth = false` (the surfaces render candidate output; only Baltor's
> governed source answers serve truth).

> **Self-contained handoff.** The full VERBATIM source of everything this doc references (the kit `oh-tokens.css`,
> `oh-components.css`, `oh-site.css`, `oh-site.jsx`, `products.js`, plus one complete app) is inlined in
> **`_repos/aidoneright/context/design/aidoneright-claude-design/DESIGN-ASSETS.md`**. Upload that file alongside this one and
> `docs/INTEGRATION-BIBLE.md`, and a designer needs nothing else from the repo. Wherever this doc names a source file
> ("see `oh-tokens.css`", "the `OhAppShell` component"), the actual code is in DESIGN-ASSETS.

**This is a near-rewrite. The prior version named `scripts/surface_server.py` as THE canonical renderer. That is
SUPERSEDED.** The canonical product is the set of full apps under `web/<app>/`, served by the showcase server over the
shared kit, with the service-plane backends behind same-origin seams. `scripts/surface_server.py` is now a lightweight
fallback only (see the one-line note in section 1). The reconciliation is recorded inside this section so the
contradiction is closed, not orphaned.

**Single sources this doc is generated from (read these; do not trust the prose over the code):**

| Source file | What it is |
|---|---|
| `scripts/showcase/server.py` | THE canonical renderer. `python3 -m scripts.showcase` serves `web/<OH_PRODUCT>/` (the full app) and proxies the service plane behind same-origin seams. `WEB_DIR = web/<OH_PRODUCT>`. |
| `_repos/teleon/frontend/kit/oh-tokens.css` | The token palette (radii, fonts, neutrals, accent, semantic colors, primitive hues) for every scope. The shipped family scope is `.oh.dir-s.theme-light`. |
| `_repos/teleon/frontend/kit/oh-components.css` | The component layer and the canonical type, spacing, and chrome scale (`--fs-*`, `--pad-*`, `--maxw-site`). Atoms: `.oh-btn`, `.oh-card`, `.oh-badge`, `.oh-table`, `.oh-field`, `.oh-input`. |
| `_repos/teleon/frontend/kit/oh-site.css` | The site and app layout CSS: top bar, hero, sections, footer, and the logged-in app shell (`.ohs-app`, `.ohs-side`, `.ohs-main`, `.ohs-topbar`). |
| `_repos/teleon/frontend/kit/oh-site.jsx` | The shared kit React components: `OhTopBar`, `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhFooter`, `OhAppShell`, `OhPageHead`, `OhRollup`, plus hooks (`useHashRoute`, `navigate`, `useSiteTheme`). |
| `_repos/teleon/frontend/kit/products.js` | The brand and product registry (single source). `PORTFOLIO.ENTITIES.<id>.accent` is the per-brand accent for Teleon, Baltor, and AIDevObserver. |
| `architecture/surface_capability_spec.json` | `pillars[]`: id, accent, brand, role, and `canonical_surface` per surface; the `serving_rule`. Source of the AI Done Right (`#5a6b87`) and OpenHubForAI (`#3b6fd4`) accents. |
| `architecture/local_service_registry.json` + `architecture/identity_realm_registry.json` | The single source of local service ports the showcase reads to build the `/api/*` and `/registry/` seams. |
| `docs/concepts/component-taxonomy-and-stages.md` | The seven primitives (Input, Knowledge Corpus, If Statement, Action, Loop, Stop/End, Output). |
| `docs/standards/DESIGN.md` + `_repos/baltor/context/standards/design-principles.md` | The existing design standards this bible extends. |

---

## 1. The one design law and the canonical stack

**ONE design system. Every surface composes the SAME shared kit. The accent color and the copy are the only
per-surface variables.**

The standardization point is stated in the code itself. `_repos/teleon/frontend/kit/oh-components.css` declares the scale as
"ONE type/space/chrome scale shared by every site. Sites differ ONLY by accent color (token scope). Padding, font
sizes, chrome dimensions and the display face are identical everywhere." A surface is therefore never styled from
scratch. It sets a root scope class and overrides one value:

```jsx
<div className={'oh dir-s theme-' + theme + ' oh-site tln'} style={{ '--accent': ACCENT }}>
```

That single line (from `_repos/teleon/frontend/teleon-main.jsx`, mirrored in `_repos/aidevobserver/frontend/aidevobserver-main.jsx`) is the
whole per-surface contract: the `oh dir-s theme-light oh-site` scope pulls in the shared tokens and components, and
`--accent` is the one brand variable.

### The canonical stack (four layers)

1. **The apps.** Five full front-end apps live under `web/<app>/`: `context-is-everything` (AI Done Right),
   `teleon`, `baltor`, `openhubforai` (OpenHubForAI), and `aidevobserver`. Each app is its own entry HTML plus a small
   brand main file (for example `_repos/teleon/frontend/index.html` + `_repos/teleon/frontend/teleon-main.jsx` + `_repos/teleon/frontend/teleon.css`).
2. **The showcase server.** `scripts/showcase/server.py` is the renderer. `OH_PRODUCT` picks the folder and
   `WEB_DIR = web/<OH_PRODUCT>` is served at the origin root. Run it with `python3 -m scripts.showcase --port <N>`.
3. **The shared kit.** Every app loads the same files from its `kit/` folder: `oh-tokens.css`, `oh-components.css`,
   `oh-site.css`, `oh-site.jsx`, and `products.js` (plus `oh-identity.js`, `oh-registry.js`, `cases.js`,
   `oh-experiments.js`). Chrome and primitive pages come from the kit; only brand config and a few bespoke pieces are
   local to the app.
4. **The service plane.** The showcase proxies same-origin seams (`/api/*`, `/registry/`, `/analytics/`) to the local
   service backends, with ports read from `architecture/local_service_registry.json` and
   `architecture/identity_realm_registry.json`. The front-end declares the bases it expects:
   `window.OPENHUBFORAI_IDENTITY_BASE = ''`, `window.OPENHUBFORAI_REGISTRY_BASE = '/registry'`, `window.OPENHUBFORAI_EVENTS_BASE = '/analytics'`.

### Reconciliation (the contradiction, closed)

- **Superseded:** the prior bible documented `scripts/surface_server.py` as THE canonical renderer, with a
  byte-identical `_CSS_TEMPLATE` and a fixed `dir-a.theme-light` palette (`--bg #faf7f0`). That described a thin
  standalone renderer, not the shipped product.
- **Canonical now:** the shipped product is the full app in `web/<app>/`, served by `python3 -m scripts.showcase`
  over the shared kit, with the service plane behind seams. The real palette is `web/<app>/kit/oh-tokens.css`,
  `.oh.dir-s.theme-light` (`--bg #fafaf8`), with the accent overridden per brand. The same conclusion is encoded in
  `architecture/surface_capability_spec.json`, whose `serving_rule` reads: "Launchers MUST serve each pillar's
  `canonical_surface` (the built-out `web/*` app)", and whose `canonical_surface` fields point at `web/context-is-everything`,
  `web/teleon`, `web/baltor`, and `web/openhubforai`.
- **`scripts/surface_server.py` is a lightweight FALLBACK only.** It can render a minimal standalone surface when the
  full app or the service plane is not available. It is not canonical and a designer never edits it to change the look.

---

## 2. The five surfaces

The family is one holding brand (AI Done Right) over four products. Each surface is a full app served by the showcase
with its own `OH_PRODUCT`. Accents come from `web/<app>/kit/products.js` (Teleon, Baltor, AIDevObserver) and from
`architecture/surface_capability_spec.json` (AI Done Right, OpenHubForAI). Roles below are written in clean product
copy (the raw spec strings are paraphrased per the copy rules in section 11).

| Brand | `OH_PRODUCT` / web dir | Accent | Role | Primary backend seam |
|---|---|---|---|---|
| AI Done Right | `context-is-everything` | `#5a6b87` (slate blue) | Parent holding brand. The portfolio home that introduces the family. | identity, registry, analytics (marketing and portfolio) |
| Teleon | `teleon` | `#6d5ef0` (indigo) | The purpose-driven, eval-gated, self-adaptive compute runtime. | `/api/teleon/` (`teleon_local_runtime`) |
| Baltor | `baltor` | `#0e7c86` (teal) | Managed, verified, provable context, powered by Teleon (governs truth). | the live-ops family (`/api/demo/`, `/api/context/`, `/api/pipeline/`, `/api/runtime/`) via `baltor_admin_demo_server` |
| AIDevObserver | `aidevobserver` | `#b25fd6` (orchid) | Reviews how a team uses AI coding agents and turns each session into a clear, ranked report. | identity, registry, analytics (review engine: `_repos/teleon/backend/src/teleon/observer`) |
| OpenHubForAI | `openhubforai` | `#3b6fd4` (royal blue) | The open registry of primitives, templates, context, tools, skills, and harnesses that Teleon, Baltor, and AIDevObserver consume, plus the open CapabilityTask spec. | `/registry/` (`local_openhubforai_projection_api`) plus `/api/components` and `/api/primitives` |

Notes. The `aidevobserver` accent (`#b25fd6`) lives only in `_repos/aidevobserver/frontend/kit/products.js`, the build-out target.
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

- **The legend and pipeline nodes.** The seven hues (`--p-*` in `_repos/teleon/frontend/kit/oh-tokens.css`) color the node chips
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
`_repos/teleon/frontend/teleon-main.jsx` and `_repos/aidevobserver/frontend/aidevobserver-main.jsx`). The accent is then overridden per brand
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

### Type scale (shared `.oh`, in `_repos/teleon/frontend/kit/oh-components.css`)

The UI font is **Inter** (`--font-sans: "Inter", -apple-system, "Segoe UI", system-ui, sans-serif`). The display face
in `dir-s` is **Hanken Grotesk** (`--font-display: "Hanken Grotesk", "Inter", sans-serif`). Mono is
`--font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace`. Light theme. The reference entry HTML
`_repos/aidevobserver/frontend/index.html` loads all three from Google Fonts (`Inter`, `Hanken Grotesk`, `JetBrains Mono`,
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
| Teleon | `#6d5ef0` | `_repos/teleon/frontend/kit/products.js` (`PORTFOLIO.ENTITIES.teleon.accent`) |
| Baltor | `#0e7c86` | `_repos/baltor/frontend/kit/products.js` (`PORTFOLIO.ENTITIES.baltor.accent`) |
| AIDevObserver | `#b25fd6` | `_repos/aidevobserver/frontend/kit/products.js` (`PORTFOLIO.ENTITIES.aidevobserver.accent`) |
| OpenHubForAI | `#3b6fd4` | `architecture/surface_capability_spec.json` |

Contrast: every accent is AA on `--panel` and `--bg`; `--accent-ink` (white) is the only thing placed on an accent
fill.

---

## 5. The shared kit components

Documented from the real components in `_repos/teleon/frontend/kit/oh-site.jsx` and the classes in `oh-site.css` and
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

### 5.9 `OhLayout` (the formal layout chooser)

The one standardized page skeleton: every page declares its shape through `OhLayout`, which composes the existing
`OhTopBar` / `OhAppShell` / `OhFooter` (it does not replace them). The `variant` prop is the chooser (`'sidebar'`,
`'one-col'`, `'two-col'`, `'no-sidebar'`; see section 6). Props:
`OhLayout({ variant, brand, nav, sidebar, cta, signInHref, theme, onToggle, footer = true, footerProps, aside, children })`.

```jsx
<OhLayout variant="no-sidebar" brand={BRAND} nav={MKT_NAV} cta={{ label: 'Start free', href: '/signup' }}
  theme={theme} onToggle={onToggle}>{page}</OhLayout>
```

### 5.10 `OhTable` (the standardized data table)

The standardized data table: a column spec plus a rows array, with optional sortable headers and click-through rows.
`cols` is `[{ key, label, render?(row), width?, align?, sortable?, sortValue?(row) }]`; `rows` is an array; `rowKey?(row)`
defaults to `row.id`; `onRow?(row)` makes rows click-through; `empty` is the empty-state text (rendered when there are
no rows); `dense` tightens the padding. A `sortable` header toggles asc, desc, off. Props:
`OhTable({ cols, rows, rowKey, onRow, empty = 'No records.', dense })`.

```jsx
<OhTable cols={[{ key: 'name', label: 'Name', sortable: true },
                { key: 'status', label: 'Status', render: r => <span className="oh-badge oh-badge--sm">{r.status}</span> }]}
  rows={records} rowKey={r => r.id} onRow={r => navigate('/browse/' + r.id)} empty="No records." />
```

### Cards, pills, table, fields

`.oh-card` is the one surface for every card and panel. `.oh-table` is the data table (uppercase 11px headers,
12px cell padding, `--line` row borders). `.oh-field` wraps a labeled input; `.oh-input` is a standalone input; both
focus to an accent border. `.oh-segment` is a pill-shaped segmented control. `.oh-kbd` renders a keyboard hint
(for example the `Command K` palette). Build new pieces from these tokens, never raw hexes.

---

## 6. Layout: two layouts, one family

Both layouts use the same kit, the same tokens, and the same accent. They differ only in chrome: marketing pages have
a top nav; logged-in pages have a left sidebar. `OhLayout` is the one chooser that unifies them: a page declares its
shape by picking a `variant`, and `OhLayout` composes the right chrome.

### `OhLayout`: the formal layout chooser (unifies both layouts)

`OhLayout` (`_repos/teleon/frontend/kit/oh-site.jsx`) is the ONE standardized page skeleton. Every page declares its shape through
it, and it composes the existing `OhTopBar`, `OhAppShell`, and `OhFooter` (it does not replace them). The `variant`
prop picks the body. The non-sidebar variants render `<OhTopBar/>`, a `.ohl-body` main, and `<OhFooter/>`; the layout
CSS is the `.ohl*` block in `_repos/teleon/frontend/kit/oh-site.css`.

| `variant` | Shape | Use for |
|---|---|---|
| `'sidebar'` | the left-sidebar logged-in app shell (delegates to `OhAppShell`; pass `sidebar` = the app nav, shape `[[href, glyph, label], ...]`) | the logged-in app |
| `'one-col'` | a centered readable single column (max-width 820px) with the top nav and footer | docs, settings, simple forms |
| `'two-col'` | main content (`children`) plus a sticky right `aside` (pass `aside`) | content with a rail |
| `'no-sidebar'` | full-width content (the default site width) with the top nav and footer | marketing, wide tables and browsers |

Full prop signature: `OhLayout({ variant, brand, nav, sidebar, cta, signInHref, theme, onToggle, footer = true, footerProps, aside, children })`.

```jsx
// a sidebar-variant page (the logged-in app): pass the app nav as `sidebar`
<OhLayout variant="sidebar" brand={BRAND} sidebar={APP_NAV} cta={{ label: '+ New run', href: '/runs' }}
  theme={theme} onToggle={onToggle}>{page}</OhLayout>

// a no-sidebar-variant page (marketing or a wide browser): pass the marketing nav as `nav`
<OhLayout variant="no-sidebar" brand={BRAND} nav={MKT_NAV} cta={{ label: 'Start free', href: '/signup' }}
  theme={theme} onToggle={onToggle}>{page}</OhLayout>
```

### 6a. Marketing and home pages (the public pattern)

Top nav, hero, sections, cards, band, footer. This is `_repos/teleon/frontend/index.html` plus `_repos/teleon/frontend/teleon-main.jsx`
(`Landing`), and `_repos/aidevobserver/frontend/aidevobserver-main.jsx` (`Landing`). The structure:

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
`OhAppShell` (`_repos/teleon/frontend/kit/oh-site.jsx`), which `_repos/teleon/frontend/teleon-main.jsx` uses for its logged-in routes
(`APP_NAV`). Existing logged-in surfaces in the same family: the Teleon Control Tower
(`_repos/teleon/frontend/Teleon PurposeTask Control Tower.html`), the Baltor dashboards (`_repos/baltor/frontend/dashboard.html` and the
guided demos), and the OpenHubForAI admin demo (`_repos/openhubforai/frontend/admin-demo.html`).

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

## 7. Page skeletons (copy-paste HTML/JSX)

Three real, copy-pasteable skeletons drawn from the live `web/teleon` app. Copy one, swap the brand config and the
copy, and you have a page that boots. Every structural value (the script order, the prop shapes, the scope class) is
verbatim from the source; the example marketing copy follows the copy rules in section 11 (no placeholders, no em or
en dashes). For the frontend-to-backend seam a page's `fetch` rides on, see `docs/INTEGRATION-BIBLE.md` (do not
duplicate the seam table here).

### 7.1 The boot skeleton (the entry HTML)

This is the whole entry document: a `<head>` that loads the three kit stylesheets plus the brand stylesheet, an empty
`<div id="root">`, the same-origin seam globals, the three vendored runtime scripts, the kit data modules, then the two
`text/babel` modules (the kit, then the brand main). Quoted from `_repos/teleon/frontend/index.html` (the shipped file is
generated by `scripts/port_full_design_to_web.py`, so do not hand-edit it; edit the bundle source or the port script
and re-run).

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:,">
<title>Teleon.dev, the purpose-driven runtime</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="kit/oh-tokens.css" />
<link rel="stylesheet" href="kit/oh-components.css" />
<link rel="stylesheet" href="kit/oh-site.css" />
<link rel="stylesheet" href="teleon.css" />
<style> html, body { margin: 0; height: 100%; scroll-behavior: smooth; } </style>
</head>
<body>
<div id="root"></div>

<script>/* same-origin service seams: scripts/showcase/server.py proxies identity, registry, analytics */
window.OPENHUBFORAI_IDENTITY_BASE = '';
window.OPENHUBFORAI_REGISTRY_BASE = '/registry';
window.OPENHUBFORAI_EVENTS_BASE = '/analytics';
</script>
<script src="/vendor/react.development.js"></script>
<script src="/vendor/react-dom.development.js"></script>
<script src="/vendor/babel.min.js"></script>

<script src="kit/products.js"></script>
<script src="kit/oh-identity.js"></script>
<script src="kit/oh-registry.js"></script>
<script src="kit/cases.js"></script>
<script src="kit/oh-experiments.js"></script>
<script src="teleon-live.js"></script>
<script type="text/babel" src="kit/oh-site.jsx"></script>
<script type="text/babel" src="teleon-main.jsx"></script>
</body>
</html>
```

Load order is load-bearing, do not reorder it:

1. **Stylesheets:** the three kit files (`kit/oh-tokens.css`, `kit/oh-components.css`, `kit/oh-site.css`) then the
   brand file (`teleon.css`). Tokens before components before layout before the brand override.
2. **Runtime:** `react.development.js`, `react-dom.development.js`, `babel.min.js` from `/vendor/` (the showcase mounts
   `web/vendor/` there, so it loads offline).
3. **Kit data modules as plain scripts:** `products.js` (sets `window.PRODUCTS`, `window.BRAND`, `window.PORTFOLIO`),
   then `oh-identity.js`, `oh-registry.js`, `cases.js`, `oh-experiments.js`, then the brand live seam (`teleon-live.js`).
   These run before any JSX so the kit components can read their window globals.
4. **JSX modules last, `type="text/babel"`:** `kit/oh-site.jsx` (the shared components, exported onto `window` at the
   end of the file) then the brand main (`teleon-main.jsx`), which uses those globals. Babel compiles both in the
   browser. There is no build step in this dev floor.

### 7.2 A complete MARKETING page skeleton (top nav, hero, sections, band, footer)

The public pattern. Read the brand config from `products.js`, set the one accent inline, and compose the chrome from
the kit. Prop shapes are exact: `nav` is `[[label, href], ...]`, `cta` is `{ label, href }`, hero `ctas` are
`[{ label, href, primary? }, ...]`, `OhFeatures` items are `[[glyph, title, desc], ...]`, and `OhFooter` `cols` are
`[[heading, [[label, href], ...]], ...]`. Modeled on `Landing` in `_repos/teleon/frontend/teleon-main.jsx`.

```jsx
const T = PORTFOLIO.ENTITIES.teleon;                      // brand entry from kit/products.js
const BRAND = { name: 'Teleon', tld: '.dev', glyph: '⟳', accent: T.accent };
const ACCENT = T.accent;                                  // the one per-surface variable

const MKT_NAV = [['How it works', '/#how'], ['Lifecycle', '/#lifecycle'], ['Pricing', '/pricing'], ['Docs', '/docs']];

function Landing({ theme, onToggle }) {
  return (
    <div className={'oh dir-s theme-' + theme + ' oh-site tln'} style={{ '--accent': ACCENT }}>
      <OhTopBar brand={BRAND} nav={MKT_NAV} cta={{ label: 'Start free', href: '/signup' }}
        signInHref="/signin" theme={theme} onToggle={onToggle} />

      <OhHero
        eyebrow="Capabilities, not code"
        title={<>Define the <span className="tint">outcome</span>.<br />We prove the rest.</>}
        lede="Set the outcome and the guardrails. Teleon turns an unbounded agent task into a deterministic capability, proves it on real examples before anything ships, and runs at a fraction of an agent's token cost."
        ctas={[{ label: 'Start free', href: '/signup', primary: true }, { label: 'See how it works', href: '/#how' }]}
        aside={<TeleonHeroCard />} />

      <OhSection id="how" label="How it works" title="Unbounded in. Deterministic, proven, and cheap out."
        body={<>Describe an outcome and the guardrails it must respect. Teleon works out the approach, proves it on
          real examples, and locks it into a deterministic capability.</>}>
        <OhFeatures items={[
          ['◎', 'Outcomes and guardrails', 'You define what good looks like and the limits it must stay within.'],
          ['◇', 'Unbounded to deterministic', 'It collapses an open-ended agent task into a fixed, repeatable capability.'],
          ['⟳', 'Self-improving, far cheaper', 'It re-proves itself when sources change, at a fraction of an agent token bill.'],
        ]} />
      </OhSection>

      <OhBand title="Define capabilities. Not infrastructure."
        sub="Outcomes and guardrails in. A deterministic, self-improving capability out."
        ctas={[{ label: 'Start free', href: '/signup', primary: true }, { label: 'Read the docs', href: '/docs' }]} />

      <OhFooter brand={BRAND} tagline={`${T.kind} · part of AI Done Right`} cols={[
        ['Product', [['How it works', '/#how'], ['Pricing', '/pricing'], ['Case studies', '/cases']]],
        ['Developers', [['Docs', '/docs'], ['Library', '/registry']]],
        ['Family', [['AI Done Right', '../context-is-everything/index.html'], ['Baltor', '../baltor/index.html']]],
      ]} />
    </div>
  );
}
```

`TeleonHeroCard` is a bespoke `.oh-card` aside (an optional second column for the hero); build it from tokens and the
`.oh-*` atoms in the brand file. Everything else here is shared kit.

### 7.3 A complete LOGGED-IN page skeleton (the OhAppShell left-sidebar shell)

The app pattern. `OhAppShell` is the left-sidebar shell. Its real prop shape, quoted verbatim from
`_repos/teleon/frontend/kit/oh-site.jsx`:

```jsx
// nav: [ [href, glyph, label], … ] (flat)  OR  groups: [ {label, items:[[href,glyph,label]], defaultOpen} ]
// optional slots: header (above nav, e.g. a pinned action), foot (replaces default footer),
// topbar (a sticky bar above the page), isActive(href) (override active detection).
function OhAppShell({ brand, nav, groups, header, foot, topbar, isActive, route, cta, theme, onToggle, children }) {
```

The sidebar `nav` is a flat `[[href, glyph, label], ...]` list (use `groups` for a longer app). The root reads the
hash route, picks the page, and wraps it in the shell. Modeled on `App` and `APP_NAV` in `_repos/teleon/frontend/teleon-main.jsx`:

```jsx
const APP_NAV = [
  ['/dashboard', '▤', 'Dashboard'],
  ['/app', '◈', 'Capabilities'],
  ['/runs', '⊕', 'Build'],
  ['/evidence', '✓', 'Evidence'],
  ['/keys', '⚿', 'API keys'],
  ['/settings', '⚙', 'Settings'],
];

function Capabilities() {                                  // one logged-in page
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Workspace" title="Capabilities"
        sub="Each capability ships only after it clears your success criteria, or rolls back."
        actions={<button className="oh-btn oh-btn--primary" onClick={() => navigate('/runs')}>+ New capability</button>} />
      <OhRollup items={[['Capabilities', 4], ['Promoted', 2], ['In eval', 1], ['Avg score', '0.90']]} />
      <div className="oh-card oh-card--pad">
        <table className="oh-table">
          <thead><tr><th>Capability</th><th>Status</th><th>Eval score</th></tr></thead>
          <tbody>
            <tr><td>State usury-rate finder</td>
              <td><span className="oh-badge oh-badge--verified oh-badge--sm">promoted</span></td>
              <td className="mono">0.96</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function App() {
  const route = useHashRoute();                            // kit hash router
  const [theme, toggle] = useSiteTheme('teleon-theme');
  const rootCls = 'oh dir-s theme-' + theme + ' oh-site tln';
  const rootStyle = { '--accent': ACCENT };

  let page;
  if (route === '/app') page = <Capabilities />;
  else page = <OhDashboard stats={[['Capabilities', 4], ['Promotions', '38']]} activity={[]} quick={[]} />;

  return (
    <div className={rootCls} style={rootStyle}>
      <OhAppShell brand={BRAND} nav={APP_NAV} route={route} cta={{ label: '+ New run', href: '/runs' }}
        theme={theme} onToggle={toggle}
        header={<button className="ohs-side-search">Search <span className="oh-kbd">⌘K</span></button>}>
        {page}
      </OhAppShell>
    </div>
  );
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

The shell highlights the active sidebar item with `route === href || route.startsWith(href + '/')`. Every page opens
with `OhPageHead`, usually an `OhRollup`, then `.oh-card` content. The page is identical in tokens, type, and atoms to
the marketing pages; only the chrome changed from a top nav to a left sidebar.

---

## 8. Framework and scaffolding

The exact stack, the router contract, and how the showcase serves it. Nothing here is a framework you install; it is
loaded from `/vendor/` at runtime.

### The stack

- **React 18** (the UMD development builds `react.development.js` and `react-dom.development.js`) plus **Babel
  standalone** (`babel.min.js`), all three vendored under `web/vendor/` and mounted by the showcase at `/vendor/`.
  The root mounts with the React 18 API: `ReactDOM.createRoot(document.getElementById('root')).render(<App />)`.
- **JSX compiled in the browser.** Each app file is a `<script type="text/babel">`, so there is no build step in the
  dev floor (a precompiled production build is a known gap, tracked in
  `_repos/aidoneright/context/design/aidoneright-claude-design/HANDOFF.md`).
- **The shared kit** (`web/<app>/kit/`): `oh-site.jsx` (the React components and hooks, written onto `window` by an
  `Object.assign(window, { ... })` at the end of the file), the three stylesheets (`oh-tokens.css`,
  `oh-components.css`, `oh-site.css`), and the data modules. `products.js` runs first and publishes
  `window.PRODUCTS`, `window.BRAND`, and `window.PORTFOLIO` (the brand and accent registry); `oh-identity.js`
  publishes `window.OHIdentity`; `cases.js` publishes `window.CASES`; `oh-experiments.js` publishes `window.OHExp`.
  The brand main reads these globals, so the kit data scripts must load before the `text/babel` modules.

### The hash-router contract

The kit ships its own router in `_repos/teleon/frontend/kit/oh-site.jsx`. There is no React Router. The contract is two functions
plus a theme hook, quoted verbatim:

```jsx
function useHashRoute() {
  const [route, setRoute] = React.useState(() => window.location.hash.slice(1) || '/');
  React.useEffect(() => {
    const on = () => setRoute(window.location.hash.slice(1) || '/');
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}
function navigate(to) { window.location.hash = to; }
```

- `useHashRoute()` returns the current route string, the hash with its leading `#` removed, defaulting to `'/'`.
- `navigate(to)` sets `window.location.hash = to`; the `hashchange` listener re-renders. Kit chrome calls it for you
  (`OhTopBar`, `OhAppShell`, `OhFooter` links all call `navigate`).
- Routes are plain strings: `'/'` (home), `'/dashboard'`, `'/keys'`, and so on. A marketing in-page link uses
  `'/#how'`, which the brand main maps back to the landing so the section with `id="how"` scrolls into view.
- `useSiteTheme('teleon-theme')` returns `[theme, toggle]` and persists `light` or `dark` to `localStorage`; pass both
  into the chrome (`theme`, `onToggle`).

The whole App is a `switch` over `useHashRoute()` that returns a marketing page, an auth page, or the `OhAppShell` with
the chosen page (see `App` in `_repos/teleon/frontend/teleon-main.jsx`).

### How the showcase serves it

`scripts/showcase/server.py` is the renderer. `OH_PRODUCT` selects the app folder; the folder is served at the origin
root, and `/vendor/` plus the `/api/*` and `/registry/` seams are mounted alongside it:

```python
OH_PRODUCT = os.environ.get("OH_PRODUCT", "").strip() or "openhubforai"
WEB_DIR = _REPO_DIR / "web" / OH_PRODUCT          # this product's front-end, served at /
VENDOR_DIR = _REPO_DIR / "web" / "vendor"          # the pinned React + Babel runtime, served at /vendor/
```

Run a surface with `OH_PRODUCT=teleon python3 -m scripts.showcase --port 8001`. The server also proxies same-origin
seams (`/api/identity/`, `/registry/`, `/analytics/`, `/api/teleon/`, `/api/observer/`, and more) to the local
service plane, with ports read from `architecture/local_service_registry.json` and the host overridable per seam by an
`OH_SEAM_*_BASE` env in the cloud. The full seam table and the FE-to-BE recipe live in `docs/INTEGRATION-BIBLE.md`;
the page just calls `fetch('/api/<service>/...')` and the showcase routes it. The same front-end code runs locally and
in the cloud; only the seam base values differ.

---

## 9. Scaffolding primitives (how to add X)

Step recipes for the four things a designer or coding agent adds most. Each one differs from the family only by accent
and copy (the law in section 1), so each recipe is short.

### 9.1 Add a new surface

1. Copy an existing app folder: `cp -r _repos/teleon/frontend web/<newbrand>` (keep `index.html`, the `kit/` folder, the brand
   main, and the brand stylesheet).
2. Add the brand entry to `web/<newbrand>/kit/products.js` under `PORTFOLIO.ENTITIES.<id>` with its `name`, `glyph`,
   and `accent` (the single source for that surface accent), so `PORTFOLIO.ENTITIES.<id>.accent` resolves.
3. In the brand main (`web/<newbrand>/<newbrand>-main.jsx`), point the brand config at that entry and keep the one
   scope line: `const T = PORTFOLIO.ENTITIES.<id>; const ACCENT = T.accent;` then render inside
   `<div className={'oh dir-s theme-' + theme + ' oh-site'} style={{ '--accent': ACCENT }}>`.
4. Rename the entry HTML script tags to the new brand main and stylesheet; leave the `/vendor/` and `kit/` script order
   exactly as in section 7.1.
5. Serve it: `OH_PRODUCT=<newbrand> python3 -m scripts.showcase --port <N>`. Register the brand and accent in
   `architecture/surface_capability_spec.json` if it is a tracked family surface. Nothing in the kit changes.

### 9.2 Add a new marketing page

1. Pick a route string (for a full page, `'/fits'`; for an in-page section, an `id` reached by `'/#fits'`).
2. Build the body from kit sections: an `OhSection` (with `id`, `label`, `title`, `body`, and `children`), an
   `OhFeatures` grid, an optional `OhBand`.
3. Wrap it in the marketing chrome so it keeps the top nav and footer. The pattern is a small `MarketingShell`
   (`OhTopBar` + `children` + `OhFooter`); see `MarketingShell` in `_repos/teleon/frontend/teleon-main.jsx`.
4. Add a route branch in `App()`: `if (route === '/fits') return <MarketingShell ...><WhereFits /></MarketingShell>;`
5. Add the nav entry to `MKT_NAV` as `['Where it fits', '/fits']` so it appears in the top bar.

```jsx
function WhereFits() {
  return (
    <OhSection id="fits" label="Where it fits" title="Built to run on your stack, not replace it."
      body="Teleon composes with the orchestration, eval, and sandbox tools you already run.">
      <OhFeatures items={[['↔', 'Runs on your runtime', 'Use your durable execution engine as a backend.']]} />
    </OhSection>
  );
}
```

### 9.3 Add a new logged-in view

1. Write the page as a `.ohs-page` that opens with `OhPageHead`, then an optional `OhRollup`, then `.oh-card` content
   (a `.oh-table`, fields, or a bespoke token-built card).
2. Add an else-if branch in `App()` that sets `page` for the route: `else if (route === '/evidence') page = <Evidence />;`
3. Add the sidebar item to `APP_NAV` as `['/evidence', '✓', 'Evidence']` (the `[href, glyph, label]` shape). The shell
   renders it and marks it active when the route matches.

```jsx
function Evidence() {
  return (
    <div className="ohs-page">
      <OhPageHead eyebrow="Proof" title="Evidence"
        sub="The proof behind every capability: what was tried, how it scored, and why it shipped." />
      <OhRollup items={[['Promotions', 38], ['Rollbacks', 6], ['Avg score', '0.90']]} />
      <div className="oh-card oh-card--pad">A token-built panel: build it from var(--token) and the .oh-* atoms.</div>
    </div>
  );
}
```

### 9.4 Add a new shared component

1. Add the function to `_repos/teleon/frontend/kit/oh-site.jsx`, building only from `var(--token)` values and the `.oh-*` atoms
   (`.oh-card`, `.oh-btn`, `.oh-badge`, `.oh-table`), never a raw hex.
2. Export it: add it to the `Object.assign(window, { ... })` block at the end of the file so the brand mains can use it.
3. Use it in any brand main. Because the kit is shared by every surface, a kit component must stay brand-agnostic; a
   piece that is specific to one surface belongs in `web/<app>/<app>.css` plus that brand main, not the kit.

```jsx
// in _repos/teleon/frontend/kit/oh-site.jsx
function OhStatPair({ label, value }) {
  return <div className="oh-card ohs-roll"><div className="v">{value}</div><div className="k">{label}</div></div>;
}
// ... then at the bottom:
Object.assign(window, { /* existing exports, */ OhStatPair });

// in any brand main:
<OhStatPair label="Avg score" value="0.90" />
```

For the backend side of any new view (the service a page's `fetch` talks to), follow the recipe in
`docs/INTEGRATION-BIBLE.md` (build the service, register its port, add one seam line, then `fetch('/api/<x>/...')`).
Do not duplicate that seam contract in this design doc.

---

## 10. Consistency rules

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

## 11. Copy rules (hard rules)

These are owner design rules. They are not suggestions. They extend `docs/standards/DESIGN.md` and
`_repos/baltor/context/standards/design-principles.md`. Follow them in product copy and in this bible's own prose.

1. **No placeholders.** Write the real name and the real words. Write "OpenHubForAI", never "OpenHubForAI registries". Write
   "AIDevObserver", "AI Done Right", "Teleon", "Baltor". No "Lorem ipsum", no "TODO", no "coming soon", no "[brand]".
   Every visible string ships as final copy.
   - Wrong: "OpenHubForAI registries, coming soon." Right: "OpenHubForAI: the open registry Teleon, Baltor, and AIDevObserver consume."
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

## 12. Claude Design handoff: build out the AIDevObserver product design

AIDevObserver (`_repos/aidevobserver/frontend/`, accent `#b25fd6`) currently ships the marketing app
(`aidevobserver-main.jsx` renders `Landing` only). The build-out is the **logged-in app**: the left-sidebar shell and
its views. The review engine backend is `_repos/teleon/backend/src/teleon/observer`; this handoff is the front-end design.

### The logged-in app shell (left sidebar)

Use `OhAppShell` with the AIDevObserver accent. Sidebar nav (the `[href, glyph, label]` shape used by `APP_NAV` in
`_repos/teleon/frontend/teleon-main.jsx`):

| Route | Glyph idea | Label | View |
|---|---|---|---|
| `/sessions` | `▤` | Sessions | The list of reviewed AI coding sessions (an `OhRollup` plus an `.oh-table`: session, surface, duration, top finding, confidence). |
| `/review` | `◉` | Review report | The full ranked report for one session: a summary card, then the ranked findings. |
| `/findings` | `⚑` | Findings | Findings across sessions, filterable by type and severity, each with a confidence bar. |
| `/settings` | `⚙` | Settings | Surfaces (VS Code, Cursor, Claude Code MCP, CLI), what is reviewed, retention. |

### The review-report view (ranked findings plus confidence)

Reuse the bespoke pieces already in `_repos/aidevobserver/frontend/aidevobserver.css`: `.ado-finding` (a finding row with a
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
| The AIDevObserver accent (`#b25fd6` in `_repos/aidevobserver/frontend/kit/products.js`). | The shared kit: `oh-tokens.css`, `oh-components.css`, `oh-site.css`, `oh-site.jsx`, `products.js`. Edit per-app files, never the kit, to change one surface. |
| Brand copy and section text in `aidevobserver-main.jsx`. | The two-layout family: marketing is top nav plus hero; logged-in is the `OhAppShell` left sidebar. Do not invent a third chrome. |
| Add a bespoke, token-built piece in `_repos/aidevobserver/frontend/aidevobserver.css` (a new card, a chart). | The copy rules in section 11 (no placeholders, no em or en dashes, no strategy leakage). |
| New app pages and routes for the logged-in views above. | The accent-only per-surface rule: never add a per-surface fork of the kit or a parallel token scale. |

### Read order for the designer

1. This doc, sections 1, 2, 6, 10, 11 (the stack, the surfaces, the two layouts, consistency, copy rules), plus
   sections 7, 8, 9 (the copy-paste page skeletons, the framework and scaffolding stack, and the how-to-add-X recipes).
2. `_repos/aidevobserver/frontend/aidevobserver-main.jsx` and `_repos/aidevobserver/frontend/aidevobserver.css` (the existing marketing app and
   its bespoke pieces).
3. `_repos/teleon/frontend/teleon-main.jsx` (the reference for the `OhAppShell` left-sidebar logged-in app: `App`, `APP_NAV`).
4. `_repos/teleon/frontend/kit/oh-site.jsx` (the kit components and `OhAppShell`) and `_repos/teleon/frontend/kit/oh-tokens.css` (the tokens).
5. `_repos/openhubforai/frontend/admin-demo.html` and `_repos/teleon/frontend/Teleon PurposeTask Control Tower.html` (existing logged-in
   dashboards in the family).

---

## Appendix: file map

| Concern | File |
|---|---|
| Canonical renderer (`OH_PRODUCT`, `WEB_DIR`, seams) | `scripts/showcase/server.py` (run `python3 -m scripts.showcase`) |
| Lightweight fallback renderer (not canonical) | `scripts/surface_server.py` |
| Tokens (palette, fonts, primitive hues) | `_repos/teleon/frontend/kit/oh-tokens.css` |
| Components and type scale | `_repos/teleon/frontend/kit/oh-components.css` |
| Site and app-shell layout CSS | `_repos/teleon/frontend/kit/oh-site.css` |
| Shared kit React components and hooks | `_repos/teleon/frontend/kit/oh-site.jsx` |
| Brand and product registry (accents) | `_repos/teleon/frontend/kit/products.js`, `_repos/aidevobserver/frontend/kit/products.js` |
| Surface spec (id, accent, brand, role, canonical_surface) | `architecture/surface_capability_spec.json` |
| Service-plane ports | `architecture/local_service_registry.json`, `architecture/identity_realm_registry.json` |
| The seven primitives | `docs/concepts/component-taxonomy-and-stages.md` |
| Existing design standards | `docs/standards/DESIGN.md`, `_repos/baltor/context/standards/design-principles.md` |
| Teleon marketing app | `_repos/teleon/frontend/index.html`, `_repos/teleon/frontend/teleon-main.jsx`, `_repos/teleon/frontend/teleon.css` |
| AIDevObserver app (build-out target) | `_repos/aidevobserver/frontend/index.html`, `_repos/aidevobserver/frontend/aidevobserver-main.jsx`, `_repos/aidevobserver/frontend/aidevobserver.css` |
| Logged-in dashboard references | `_repos/openhubforai/frontend/admin-demo.html`, `_repos/baltor/frontend/dashboard.html` |
| Context-freshness guard (this is 1 of the 5 canonical docs) | `scripts/check_context_freshness.py` |
