# START HERE — Claude design (AI Done Right · one screen)

You are the designer ("Claude design"). The handoff is **three self-contained files** (uploaded with this one); you
do not need the repo. There is ONE shared kit: all 5 surfaces import it and differ ONLY by accent and copy. Read in
this order, then design.

## Read order (top to bottom)

1. **`DESIGN-BIBLE.md`** (the GUIDE): tokens, type scale, every component, the two layouts (marketing top-nav
   plus the `OhAppShell` left-sidebar logged-in shell), routes, governance, the copy rules, and the SAFE-vs-LOCKED
   handoff. This is the #1 read.
2. **`DESIGN-ASSETS.md`** (in this folder, the SOURCE): the full shared kit verbatim (`oh-tokens.css`,
   `oh-components.css`, `oh-site.css`, `oh-site.jsx`, `products.js`) plus one COMPLETE app (Teleon). When the guide
   says "see `oh-tokens.css`" or names a component, the actual code is here. This is the thing you edit once and it
   applies to all 5 surfaces.
3. **`CONSISTENCY-CONTRACT.md`** (the cross-surface rulebook): the SAME header / footer / logged-in shell /
   layout skeletons / primitives for every surface — differ ONLY by accent + copy. Read it before building a second surface.
4. **`SAAS-PAGE-INVENTORY.md`** (EVERY SaaS page — login, sign-up, reset password, account, billing, subscription, team, developer, system — each mapped to its kit component + one of the three standard layouts). The complete checklist so no internal page is missed.
5. **`INTEGRATION-BIBLE.md`**: how a frontend talks to a backend (same-origin seams), local and cloud.
6. **The 5 live URLs** (below): see it rendered.

The live renderer is the showcase serving the full `web/<brand>/` apps over the shared kit. `scripts/surface_server.py`
is a demoted fallback; do not design against it.

Then: `FAMILY-README.md` + `HANDOFF.md` (next to this file) for family shape, the Baltor method spine, and
production gaps.

## Framework, kit, and page skeletons (build pages without guessing)

`DESIGN-BIBLE.md` now carries concrete, copy-paste HTML and JSX so you can build a page without inventing an API.
Read these three, in order:

1. **`DESIGN-BIBLE.md` sections 7, 8, 9.** Section 7 (Page skeletons) has the exact boot HTML, a full marketing
   page, and a full logged-in `OhAppShell` page, all copy-pasteable. Section 8 (Framework and scaffolding) has the
   stack (React 18 plus in-browser Babel), the hash-router contract (`useHashRoute()` returns the route,
   `navigate(to)` sets the hash), and how the showcase serves it. Section 9 (Scaffolding primitives) is the
   how-to-add-X recipes: a new surface, a new marketing page, a new logged-in view, a new shared component.
2. **The kit itself — inlined verbatim in `DESIGN-ASSETS.md`** (sections 1-6, nothing external): the shared
   components + hooks (`OhTopBar`, `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhFooter`, `OhAppShell`,
   `OhLayout`, `OhTable`, `OhPageHead`, `OhRollup`, plus `useHashRoute`/`navigate`/`useSiteTheme`), the token palette,
   and one COMPLETE worked app (Teleon). **To BUILD AIDevObserver, open `AIDevObserver-app-STARTER.html` in this
   folder** — the complete five-screen app, already working; elevate it (see `AIDevObserver-BRIEF.md` → OUTPUT
   CONTRACT). Do not design a single comp.
3. **`INTEGRATION-BIBLE.md`.** The frontend-to-backend seam: a page calls a same-origin path
   (`/api/<service>/...` or `/registry/...`) and the showcase routes it to the backend, so the page code is the same
   locally and in the cloud.

**The canonical build stack (per `DESIGN-BIBLE.md` section 1).** The shipped product is the set of full apps
under `web/<app>/` (`context-is-everything`, `teleon`, `baltor`, `openhubforai`, `aidevobserver`), served by
`python3 -m scripts.showcase` (the `OH_PRODUCT` env picks `web/<product>/`), over the shared kit in `web/<app>/kit/`
(`oh-site.jsx`, `oh-tokens.css`, `oh-components.css`, `oh-site.css`, `products.js`). Framework: React 18 plus ReactDOM
plus in-browser Babel (all vendored at `/vendor/`), JSX as `<script type="text/babel">`, hash routing via the kit.
Light theme, Inter, one per-brand accent. `scripts/surface_server.py` is a lightweight fallback renderer, not the
canonical one. The kit top bar has no portfolio dropdown and always shows a `Demo` nav link.

## The 5 surfaces + accents + live URLs

(single source: `architecture/surface_capability_spec.json` → `scripts/_surface_accents.py`; URLs in `dist/surface-urls.json`)

| Surface | `--accent` | live URL (ephemeral TryCloudflare tunnel) |
|---|---|---|
| **AI Done Right** (hub) | `#5a6b87` | https://flags-employee-robinson-nevada.trycloudflare.com |
| **Teleon** | `#6d5ef0` | https://commodities-cleaner-entities-dangerous.trycloudflare.com |
| **Baltor** | `#0e7c86` | https://marathon-crop-moore-logistics.trycloudflare.com |
| **AIDevObserver** | `#b25fd6` | https://somerset-evaluations-schedules-copying.trycloudflare.com |
| **OpenHubForAI** (carries `/browse`) | `#3b6fd4` | https://chancellor-photography-coins-cir.trycloudflare.com |

> URLs rotate every launch — `dist/surface-urls.json` is the live record; production uses the stable domains.

## Your job

Elevate the live `surface_server` pages toward the richness of the `dist/sites/aidoneright-design/` bundle —
**WHILE keeping the byte-identical-CSS law.** You never style a single surface. You edit `_CSS_TEMPLATE` once and the
change propagates to all 5. After any change: `python3 scripts/check_surface_server.py --self-test` (122 assertions).

## SAFE to change (single-source — propagates to all 5)

- A surface's **accent** or **copy** → `architecture/surface_capability_spec.json`.
- **Type scale, spacing, color tokens, component CSS** → `_CSS_TEMPLATE` in `scripts/surface_server.py` (ONE place;
  use `var(--token)`s, never raw hexes).
- **Add a component** → add its CSS to `_CSS_TEMPLATE` **and** emit its HTML in the relevant `render_*` helper.

## LOCKED (owner law — do not break)

- The **byte-identical-CSS law**: accent + copy are the ONLY per-surface variables. No per-surface stylesheet, no
  surface-varying inline style, no second accent-like token.
- The **5-surface model**, and that only **OpenHubForAI** owns `/browse`.
- The **governance footer** + **`serves_truth = false`** + the never-store / never-echo BYO-key contract.
- **Inter UI + `ui-monospace`** as the canonical fonts (resizing within the scale is fine; changing the type
  *system* needs owner intent).

Full detail for every line above: **`DESIGN-BIBLE.md`** §12 (the SAFE-vs-LOCKED handoff). `serves_truth = false` (candidate output, not
verified truth; a BYO key is used only for the request, never stored or logged).
