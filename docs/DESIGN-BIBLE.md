# THE DESIGN BIBLE — AI Done Right · the single design + UX reference

> The visual/UX counterpart to `docs/BIBLE.md` (which is the *what + why + laws*). This is the **how it looks + how it's
> built**: the one design system, the tokens, the per-brand color schemes, the components, the routing, and every design
> decision. If a surface disagrees with this, fix the surface. Colors/values here name their **single-source file**
> (never re-hardcode a hex — No-Magic-Values applies to design too). Last reconciled **2026-06-25**.

---

## 0. The one law of this file

**ONE design system. Every surface — AI Done Right · Teleon · Baltor · AIDevObserver · Open\*Hubs (OpenHubForAI.io) —
shares the SAME layout, HTML structure, CSS, fonts, and components. They differ ONLY in color scheme + copy.** Enforced
by `scripts/check_northstar_design.py` (kit-consistency + no placeholders). No side designs, no per-surface forks, no
placeholder/dummy content.

---

## 1. The shared kit (the design system — single source)

Lives in `dist/sites/openharness-design/shared/` (the tracked design source-of-record), loaded by every surface's
loader HTML before its `*-main.jsx`:

| File | Role |
|---|---|
| `oh-tokens.css` | **design tokens** — color/spacing/type variables, light + dark themes (the color single source) |
| `oh-components.css` | component styles (cards, buttons, inputs, badges, grids) |
| `oh-site.css` | site/layout styles (top bar, hero, sections, footer, app shell) |
| `oh-site.jsx` | the **component library** (OhTopBar, OhHero, OhSection, OhCard, OhFooter, OhAppShell, OhCaseStudies, OhAuth, OhDocs, OhPricing, OhCommandK, …) |
| `oh-hub.jsx` / `oh-hub.css` | the hub/registry surface kit (the Open\*Hubs catalog UI) |
| `products.js` | the **brand registry** — every pillar/hub's name, domain, accent, glyph, blurb, status (the per-brand single source) |
| `oh-identity.js` | the auth/identity seam (login/session; honest-disabled where no live realm) |
| `oh-experiments.js` | A/B + event tracking engine — **A/B DISABLED** (owner 2026-06-25: one consistent design, `pickWeighted` returns the control variant) |
| `oh-registry.js` · `cases.js` | shared data seams (registry rows; case studies) |

**Fonts** (loaded in every surface loader): **Hanken Grotesk** (UI) + **IBM Plex Mono** (code/labels).

---

## 2. Design tokens (single source: `shared/oh-tokens.css`)

Two themes, toggled via `useSiteTheme(...)` (persisted per surface). Light: warm paper (`--bg:#faf7f0`,
`--line:#e7e0d2`, `--accent:#b8501f`). Dark: warm charcoal (`--bg:#1b1a17`, `--line:#353230`, …). NEVER hard-code a
color in a surface — read the token. The per-brand `--accent` is injected from `products.js` (next section).

---

## 3. Per-brand color schemes (single source: `shared/products.js`)

The ONLY thing that changes between surfaces. Each entry sets its `accent` (and a `futureAccent` for pre-launch hubs).
Confirmed (read from `products.js`, don't re-type):

| Surface | accent |
|---|---|
| **Teleon** | `#6d5ef0` (indigo) |
| **Baltor** | `#0e7c86` (teal) |
| Hubs (per-hub) | varied muted tones (`#2f8f6b`, `#2f7d8f`, `#8f6f2f`, OpenReviewHub `#9d4edd`, …) |

> **RESOLVED 2026-06-25:** per-surface accents are now SINGLE-SOURCED in `architecture/surface_capability_spec.json`
> (`accent` per pillar), read by the standalone servers via `scripts/_surface_accents.py` — no hard-coded hexes.
> Canonical: AI Done Right `#5a6b87` · Teleon `#6d5ef0` · AIDevObserver `#b25fd6` · Baltor `#0e7c86` · OpenHubForAI.io
> `#3b6fd4`. (Follow-up: mirror the three assigned accents into `products.js` for the design surfaces too.)

---

## 4. Components + primitives (in `oh-site.jsx`)

Marketing chrome: `OhTopBar` (nav), `OhHero`, `OhSection`, `OhBand`, `OhFeatures`, `OhFooter`, **`MarketingShell`**
(the shared wrapper that gives info pages — cases/about/status/legal — the top-bar nav + footer; added 2026-06-25 to
fix the case-study nav loss). App chrome: `OhAppShell` (left sidebar + header — ONLY for app routes, never marketing).
Content: `OhCard`, `OhCaseStudies`/`OhCaseStudy`, `OhDocs`, `OhPricing`, `OhAuth`, `OhApiKeys`, `OhStatus`,
`OhChangelog`, `OhLegal`, `OhAbout`, `OhContact`, `OhCommandK` (⌘K search). Hub UI: `oh-hub.jsx` + the faceted browse
(`scripts/openhub_browse_server.py` over `src/teleon/registry/browse.py`).

---

## 5. Routing + layout decisions

- **Hash router** (`useHashRoute()`): routes are `#/fits`, `#/cases`, `#/dashboard`, … (works as a static file).
- **Marketing vs app:** marketing/info routes render in `MarketingShell` (top-bar + footer, NO sidebar); app routes
  (`/dashboard`, `/app`, `/runs`, …) render in `OhAppShell` (sidebar). An **unknown route → a MARKETING 404**
  (`home="/"`), never the app shell (fixed 2026-06-25 — was leaking the sidebar to logged-out users).
- **Section anchors:** `/how`, `/lifecycle` are sections of the landing — routed to `<Landing>` (were 404s).

---

## 6. Design decisions (the log)

1. **5 brand pillars**, one design system (color + copy only).
2. **A/B testing disabled** — one consistent design, no split (owner 2026-06-25); the engine stays, returns control.
3. **One hub site: `OpenHubForAI.io`** (owner 2026-06-25) — all ~35 hubs + 103 registries are SECTIONS/FACETS of one
   faceted catalog (NOT 35 domains; NOT `OpenAIHub.io` — OpenAI trademark). Backend datasets stay separate.
4. **Faceted browse** — the browsable unit is the RECORD; hubs/registries are flexible facets (a record may sit under
   multiple categories). UI over the existing federated search; never rebuilt.
5. **BYO-key demos** — every surface's `/demo` takes the user's key transiently (never stored); friendly UX.
6. **Honest seams** — disabled OAuth buttons say "Social sign-in is coming soon" (no fake nav); enforced by
   `check_harness_hub_auth_wiring` / `check_bundle_full_design_wiring`.
7. **No competitive-strategy leaks in public copy** — neutralized "private until a competitor enters the lane" →
   "in private preview" everywhere (2026-06-25).
8. **Protect the expensive design work** — the design source `dist/sites/openharness-design/` is TRACKED in git;
   never deleted, only moved (archive/legacy). The root-cause fix for "the design keeps disappearing."

---

## 7. The build path (design source → live)

`dist/sites/openharness-design/` (tracked source-of-record) → `scripts/port_full_design_to_web.py --apply` → `web/`
(the served apps). Edit the design SOURCE, then port — never hand-edit `web/`. Each surface's loader HTML loads the
shared kit + its `*-main.jsx` + its `*.css`. The design tunnel serves the bundle directly.

---

## 8. Design contracts + hooks (anti-regression)

- `scripts/check_northstar_design.py` — **no placeholder/dummy/side designs** + **shared-kit consistency** (every
  product loader references the kit). Gate-enforced.
- `scripts/check_surface_and_dev_contract.py` — each pillar's BUILT-OUT canonical surface exists + non-empty.
- `architecture/surface_capability_spec.json` — the per-pillar surface + capability single source.
- `scripts/check_bundle_full_design_wiring.py` / `check_harness_hub_auth_wiring.py` — the surfaces are wired to the
  real seams (identity, honest OAuth seams, no fake nav).
- Edit-time: `scripts/hooks/hygiene_guard.py` warns on placeholders in surfaces the moment they're written.

---

## 9. The design laws (every surface change obeys)

1. ONE kit — differ only in color + copy. 2. No placeholders / dummy / orphaned / SIDE designs. 3. Honest seams (no
fake nav; disabled = clearly disabled). 4. No strategy leaks in public copy. 5. Read tokens/accents from the single
source (`oh-tokens.css` / `products.js`), never re-hardcode. 6. Edit the design SOURCE + port; protect it (move,
never delete). 7. Marketing chrome ≠ app chrome — never leak the sidebar to a logged-out/unknown route.
