# AI Done Right, Claude Design family handoff (current)

> **The handoff is three self-contained files. Upload these and you need nothing else from the repo:**
> 1. `docs/DESIGN-BIBLE.md` (the guide: tokens, type, every component, layouts, routes, governance, copy rules, the designer task)
> 2. `docs/design/openharness-claude-design/DESIGN-ASSETS.md` (the actual SOURCE, verbatim: the full shared kit CSS and React components plus one complete app)
> 3. `docs/INTEGRATION-BIBLE.md` (how the frontends talk to backends, local and cloud)
>
> If the guide says "see `oh-tokens.css`" or "the kit components", the full verbatim content is in DESIGN-ASSETS.md. Last reconciled 2026-06-26. serves_truth=false (the surfaces render candidate output; only Baltor's governed source serves truth). A BYO key is used only for the request, never stored.

## How the live system actually works (corrected)

Every surface is a React 18 app (rendered in the browser via Babel standalone, no build step) living at `web/<brand>/`. Each app imports the SAME shared kit (`web/<brand>/kit/`):

- `oh-tokens.css` (design tokens: the palette, type scale, spacing, radii, shadows, the 5 accents)
- `oh-components.css` + `oh-site.css` (the styles: atoms, the top bar, hero, sections, the `OhAppShell` left-sidebar logged-in shell)
- `oh-site.jsx` (the components: `OhTopBar`, `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhFooter`, `OhAppShell`, plus the `useHashRoute`/`navigate` hooks)
- `products.js` (the portfolio config and per-brand accents)

The apps are served by the showcase: `OH_PRODUCT=<brand> python3 -m scripts.showcase --port N` serves `web/<OH_PRODUCT>/`, and same-origin seams (`/api/identity/`, `/registry/`, `/api/teleon/`, `/api/observer/`) reach the service-plane backends (see INTEGRATION-BIBLE). All of that kit source is inlined verbatim in DESIGN-ASSETS.md.

**Note:** `scripts/surface_server.py` is a demoted lightweight FALLBACK, NOT the live renderer. Do not design against it. The live renderer is the showcase serving the `web/<brand>/` apps over the shared kit.

**The one design law:** all 5 surfaces use the SAME shared kit and differ ONLY by their accent and their copy. You never style a single surface in isolation. You edit a shared kit file once (for example a component in `oh-site.jsx` or a token in `oh-tokens.css`) and it applies to all 5. Full SAFE vs LOCKED map: DESIGN-BIBLE.

## The 5 surfaces

| Surface | accent | role | live URL (ephemeral TryCloudflare tunnel) |
|---|---|---|---|
| **AI Done Right** | `#5a6b87` | parent / holding brand, the portfolio HUB / index | https://flags-employee-robinson-nevada.trycloudflare.com |
| **Teleon** | `#6d5ef0` | purpose-driven, eval-gated, self-adaptive compute runtime | https://commodities-cleaner-entities-dangerous.trycloudflare.com |
| **Baltor** | `#0e7c86` | managed, verified, provable context, governs TRUTH | https://marathon-crop-moore-logistics.trycloudflare.com |
| **AIDevObserver** | `#b25fd6` | watches AI USAGE, reviews the SESSION (post) plus intra-session | https://somerset-evaluations-schedules-copying.trycloudflare.com |
| **OpenHubForAI** | `#3b6fd4` | the open store both products consume, carries the faceted `/browse` | https://chancellor-photography-coins-cir.trycloudflare.com |

TryCloudflare URLs rotate on every launch; the live record is `dist/surface-urls.json`. Production uses the stable domains (aidoneright.dev, teleon.dev, baltor.ai, aidevobserver.io, openhubforai.io).

## The designer task (what to build)

1. **Build the AIDevObserver logged-in app shell** using `OhAppShell` (the left sidebar: Sessions list, Review report, Findings, Settings), matching the family. The kit, the shell component, and a worked example are all in DESIGN-ASSETS.md.
2. **Elevate the marketing pages** of all 5 surfaces toward a richer, shipped-product feel, while keeping the one design law (shared kit, differ only by accent and copy).
3. **Follow the copy rules** (also enforced in DESIGN-BIBLE): no placeholders ("OpenHubForAI", never "Open*Hubs"), no em or en dashes, no strategy leakage in public copy, real sales and marketing copy.

## Brand

Parent company: **AI Done Right** (aidoneright.dev). Tagline: **AI, done right.** Thesis: discovery is not trust. Legacy folder names such as `context-is-everything/` (the AI Done Right app) stay in place for cross-link stability; displayed brand and product names are current.

## Baltor method spine (private-first registry surfaces)

| Hub | Stage | Method family |
| --- | --- | --- |
| OpenReconciliationHub | Reconcile | dedupe; link evidence; surface conflicts |
| OpenHardeningHub | Harden | detect fragile values; create durable objects; refresh over time |
| OpenEnrichmentHub | Enhance | add metadata; connect objects; increase robustness |
| OpenOptimizationHub | Optimize | summarize; structure; rank |
| OpenVerificationHub | Verify | bind claims to sources; prove by hash; hold out the unprovable |

These open the method language around Baltor's engine. They are not truth authorities; Baltor governs truth.

## Do not regress

- Do not break the one design law: the shared kit is the only style source; accent and copy are the only per-surface variables.
- Do not design against `surface_server.py` (it is a fallback, not the live renderer).
- Do not hardcode counts, colors, ports, or brand copy that has an owning source (recompute or read the spec; family count via `python3 scripts/check_ai_done_right_surface_family.py --self-test`).
- Do not present private bench hubs as public production surfaces, or present Open*Hub discovery as trust.
- Do not let Teleon own Baltor truth, or Baltor become a generic runtime.
